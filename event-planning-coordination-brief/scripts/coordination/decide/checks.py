"""Hard-constraint and condition checks for one candidate option.

Every check is a `policy.Check` with the decision evaluated, the outcome, the claims and baseline
elements it rests on, and a reason whenever the outcome is not `pass`. A check whose inputs are not
supported is `unverified` and names the blocking claims; it never passes on a missing or
conflicting value.
"""

from __future__ import annotations

from ..policy import Check, category_check, ceiling_check, prerequisite_check, vendor_status_check
from .options import Option, costs


class Evaluator:
    def __init__(self, normalized, baseline):
        self.n, self.b = normalized, baseline

    # ---- helpers -------------------------------------------------------------------------------
    def _missing(self, ids) -> list[str]:
        out = []
        for i in ids:
            if i.startswith("B-"):
                e = self.b.elements.get(i)
                if e is None or e.support != "supported":
                    out.append(f"{i} ({e.support if e else 'missing'})")
            else:
                c = self.n.get(i)
                if c is None or c.support != "supported":
                    out.append(f"{i} ({c.support if c else 'missing'})")
        return out

    def _unverified(self, cid, kind, what, ids, owner=None) -> Check:
        return Check(cid, kind, "unverified", f"{what}: cannot be evaluated; inputs not supported: "
                     f"{self._missing(ids)}.", list(ids), owner)

    def cv(self, cid):
        c = self.n.get(cid)
        return c.value if c is not None and c.support == "supported" else None

    # ---- evaluation ----------------------------------------------------------------------------
    def evaluate(self, o: Option) -> tuple[list[Check], dict]:
        p = o.id
        checks: list[Check] = []
        checks += self._date_and_keynote(p, o)
        checks += self._venue_window(p, o)
        checks += self._readiness(p, o)
        checks += self._services(p, o)
        checks += self._capacity(p, o)
        checks += self._accessibility(p, o)
        checks += self._dietary(p, o)
        checks += self._prerequisites(p, o)
        cost = costs(o, self.b)
        checks += self._budget(p, o, cost)
        return checks, cost

    def _date_and_keynote(self, p, o):
        out = []
        win, fall, key = self.b.get("B-event-window"), self.b.get("B-fallback-window"), self.b.get("B-keynote")
        if win is None:
            out.append(self._unverified(f"CHK-{p}-date", "hard", "Event date and window", ["B-event-window"], "Operations"))
        elif o.date == win["date"]:
            out.append(Check(f"CHK-{p}-date", "hard", "pass",
                             f"Event date {o.date} is the preferred window ({win['priority']}) "
                             f"{win['start'][11:16]}–{win['end'][11:16]}.", ["B-event-window"], "Operations"))
        elif fall is not None and o.date == fall["date"]:
            out.append(Check(f"CHK-{p}-date", "hard", "pass",
                             f"Event date {o.date} is the fallback window (priority {fall['priority']}).",
                             ["B-fallback-window"], "Operations"))
        else:
            out.append(Check(f"CHK-{p}-date", "hard", "fail", f"Event date {o.date} is not a calendar event window.",
                             ["B-event-window", "B-fallback-window"], "Operations"))
        if key is None:
            out.append(self._unverified(f"CHK-{p}-keynote", "hard", "Keynote availability", ["B-keynote"], "Programme"))
        elif key["date"] == o.date:
            out.append(Check(f"CHK-{p}-keynote", "hard", "pass",
                             f"Keynote available {key['start'][11:16]}–{key['end'][11:16]} on {o.date} ({key['priority']}).",
                             ["B-keynote"], key["owner"]))
        else:
            ev = ["B-keynote"]
            row = self.n.get(self.b.calendar_row_id("keynote_availability"))
            if row is not None and row.fields.get("note_facts", {}).get("keynote_unavailable_on_fallback"):
                ev.append(row.id)
            for q in o.quote_ids:
                if self.b.quotes[q].fields["facts"].get("keynote_unavailable_on_date"):
                    ev.append(self.b.quotes[q].id)
            out.append(Check(f"CHK-{p}-keynote", "hard", "fail",
                             f"The hard keynote constraint is only available on {key['date']}; on {o.date} the "
                             "keynote is unavailable.", ev, key["owner"]))
        return out

    def _venue_window(self, p, o):
        hold, cov, tear = self.b.get("B-venue-hold"), self.b.get("B-venue-coverage"), self.b.get("B-teardown")
        if hold is not None and hold["date"] == o.date:
            ok = tear is None or tear["end"] <= hold["end"]
            return [Check(f"CHK-{p}-venue-window", "hard", "pass" if ok else "fail",
                          f"Venue hold {hold['start'][11:16]}–{hold['end'][11:16]} on {o.date} covers setup and "
                          f"teardown (clear by {tear['end'][11:16] if tear else '?'}).",
                          ["B-venue-hold", "B-teardown"], "Operations")]
        if cov is not None and o.date in cov["dates"]:
            return [Check(f"CHK-{p}-venue-window", "hard", "pass",
                          f"Venue coordination record covers {o.date} {cov['start']}–{cov['end']} (case record).",
                          ["B-venue-coverage"], "Operations")]
        return [self._unverified(f"CHK-{p}-venue-window", "hard", f"Venue window on {o.date}",
                                 ["B-venue-hold", "B-venue-coverage"], "Operations")]

    def _readiness(self, p, o):
        r = self.b.get("B-readiness")
        if r is None:
            return [self._unverified(f"CHK-{p}-readiness", "hard", "Setup by opening and teardown by clear time",
                                     ["B-readiness"], "Operations")]
        services = [q for q in o.quote_ids if self.b.quotes[q].value["category"] != "venue"]
        covered = set(r["catering_alternatives"]) | set(r["common"])
        uncovered = [q for q in services if q not in covered]
        cat_count = len([q for q in services if q in r["catering_alternatives"]])
        if o.date != r["date"]:
            return [Check(f"CHK-{p}-readiness", "hard", "unverified",
                          f"Readiness is confirmed only for {r['date']}; no readiness evidence for {o.date}.",
                          ["B-readiness"], "Operations")]
        if not uncovered and cat_count == 1 and set(r["common"]) <= set(services):
            return [Check(f"CHK-{p}-readiness", "hard", "pass",
                          f"Readiness record confirms this bundle can set up {r['setup']['start']}–{r['setup']['end']} "
                          f"and clear {r['teardown']['start']}–{r['teardown']['end']} (case record; not a real test).",
                          ["B-readiness"], "Operations")]
        outcome, ev = "unverified", ["B-readiness"]
        unresolved = self.cv("N-BRIEF-readiness_unresolved_quote_conditions")
        if unresolved and unresolved in uncovered:
            outcome = "open"
            ev.append("N-BRIEF-readiness_unresolved_quote_conditions")
        return [Check(f"CHK-{p}-readiness", "hard", outcome,
                      f"Readiness by 09:30 and clearance by 18:30 is not confirmed for {uncovered or 'this bundle'}; "
                      "no vendor durations are given, so it cannot be derived.",
                      ev + ["N-BRIEF-no_vendor_durations_or_buffer"], "Operations")]

    def _services(self, p, o):
        out = []
        for gap in o.service_gaps:
            out.append(Check(f"CHK-{p}-service-{gap}", "hard", "unverified",
                             f"No {gap} quote is available on {o.date}; availability cannot be assumed.",
                             ["N-BRIEF-no_expired_quote_or_unconfirmed_availability"], "Operations"))
        venue_quotes = {q for q in o.quote_ids if self.b.quotes[q].value["category"] == "venue"}
        for q in o.quote_ids:
            c = self.b.quotes[q]
            v = c.value
            if v["available_date"] != o.date:
                out.append(Check(f"CHK-{p}-{q}-date", "hard", "fail", f"{q} is quoted for {v['available_date']}, "
                                 f"not {o.date}.", [c.id], "Operations"))
            validity = self.n.get(f"X-quote-validity-{q}")
            if c.fields["valid_at_business_clock"]:
                note = ""
                if validity is not None and validity.value.get("valid_through_decision_deadline") is False:
                    note = " It expires before the decision deadline."
                out.append(Check(f"CHK-{p}-{q}-validity", "validity", "pass",
                                 f"{q} valid until {v['valid_until']} at the business clock.{note}",
                                 [c.id] + ([validity.id] if validity else []), "Operations"))
            else:
                out.append(Check(f"CHK-{p}-{q}-validity", "validity", "unverified",
                                 f"{q} expired {v['valid_until']} before the business clock; an expired quote is not "
                                 "assumed and a refreshed quote is needed.",
                                 [c.id, "N-BRIEF-no_expired_quote_or_unconfirmed_availability"], "Operations"))
            if c.fields.get("conflicts_with") or c.fields.get("text_conflicts"):
                out.append(Check(f"CHK-{p}-{q}-terms", "hard", "unverified",
                                 f"{q} has conflicting terms ({c.fields.get('conflicts_with') or 'option vs notes'}); "
                                 "none is chosen.", [c.id, "STK-I1-L167"], "Operations"))
            if q in venue_quotes:
                continue  # venue confirmation is the named prerequisite P-venue-confirmation
            owner = (self.b.get(f"B-budget-{v['category']}") or {}).get("owner")
            out.append(vendor_status_check(f"CHK-{p}-{q}-confirmation", q, v["status"],
                                           list(c.fields.get("confirmation_evidence", [])), [c.id], owner))
        return out

    def _capacity(self, p, o):
        out = []
        head = self.b.get("B-headcount")
        q_by_cat = {}
        for q in o.quote_ids:
            q_by_cat.setdefault(self.b.quotes[q].value["category"], []).append(self.b.quotes[q])
        need = lambda n: self.b.get(f"B-need-{n}")

        def cmp(cid, what, demand, demand_ids, supply, supply_ids, owner, note=""):
            ids = demand_ids + supply_ids
            if demand is None or supply is None:
                return self._unverified(cid, "hard", what, ids, owner)
            ok = supply >= demand
            return Check(cid, "hard", "pass" if ok else "fail",
                         f"{what}: capacity {supply} for {demand} (margin {supply - demand}).{note}"
                         + ("" if ok else " Shortage; no alternative inside this option."), ids, owner)

        total = head["total"] if head else None
        for c in q_by_cat.get("venue", []):
            places = self.cv("N-BRIEF-audience_places")
            out.append(cmp(f"CHK-{p}-capacity-venue", "Audience places", total, ["B-headcount"],
                           places, ["N-BRIEF-audience_places", c.id], "Operations"))
        cats = q_by_cat.get("catering", [])
        if not cats and o.variant != "fallback-date":
            out.append(Check(f"CHK-{p}-capacity-catering", "hard", "fail", "No catering quote in this option.",
                             ["B-headcount"], "Operations"))
        for c in cats:
            out.append(cmp(f"CHK-{p}-capacity-catering-{c.value['quote_id']}",
                           f"Catering {c.value['quote_id']} for all groups incl. staff and speakers", total,
                           ["B-headcount", "STK-I3-L133"], c.value["capacity"], [c.id], "Operations",
                           note=" The register states the capacity number only; who it covers is not further "
                                "specified."))
        quiet = self.cv("N-BRIEF-quiet_space")
        staff = [c for c in q_by_cat.get("accessibility", []) if "quiet_room_staffing" in c.fields["features"]]
        if staff:
            supply = min(quiet["occupancy"], staff[0].value["capacity"]) if quiet else None
            out.append(cmp(f"CHK-{p}-capacity-quiet-room", "Quiet room (room occupancy and staffing)",
                           need("quiet_room"), ["B-need-quiet_room"], supply,
                           ["N-BRIEF-quiet_space", staff[0].id], "Learner Experience"))
        if q_by_cat.get("venue"):
            out.append(cmp(f"CHK-{p}-capacity-wheelchair", "Wheelchair spaces", need("wheelchair_seating"),
                           ["B-need-wheelchair_seating"], self.cv("N-BRIEF-wheelchair_spaces"),
                           ["N-BRIEF-wheelchair_spaces"], "Operations",
                           note=" Companions use ordinary places." if self.cv("N-BRIEF-companions_use_ordinary_places") else ""))
        for feature, nkey, label in (("live_captions", "live_captions", "Live captions"),
                                     ("hearing_loop", "hearing_loop", "Hearing loop")):
            prov = [c for c in o.quote_ids if self.b.quotes[c].fields["features"].get(feature, {}).get("value") is True]
            if prov:
                c = self.b.quotes[prov[0]]
                out.append(cmp(f"CHK-{p}-capacity-{feature}", label, need(nkey), [f"B-need-{nkey}"],
                               c.value["capacity"], [c.id], "Learner Experience"))
        for c in q_by_cat.get("security", []):
            out.append(cmp(f"CHK-{p}-capacity-security", "Security coverage", total, ["B-headcount"],
                           c.value["capacity"], [c.id], "Operations"))
        return out

    def _accessibility(self, p, o):
        """Hard provisions (STK-I2-L77): each must be evidenced by the option or the venue case record."""
        out = []
        reqs = self.b.get("B-accessibility-requirements")
        if reqs is None:
            return [self._unverified(f"CHK-{p}-access", "hard", "Accessibility provisions",
                                     ["B-accessibility-requirements"], "Learner Experience")]
        has_venue = any(self.b.quotes[q].value["category"] == "venue" for q in o.quote_ids)
        feats = {q: self.b.quotes[q].fields["features"] for q in o.quote_ids}

        def by_feature(key, label):
            yes = [q for q, f in feats.items() if f.get(key, {}).get("value") is True]
            no = [q for q, f in feats.items() if f.get(key, {}).get("value") is False]
            if yes:
                return Check(f"CHK-{p}-access-{key}", "hard", "pass", f"{label} provided by {yes}.",
                             [self.b.quotes[q].id for q in yes] + ["STK-I2-L77"], "Learner Experience")
            if no:
                return Check(f"CHK-{p}-access-{key}", "hard", "fail",
                             f"{label} is a hard requirement and {no} explicitly excludes it; no other quote in "
                             "this option provides it. Accessibility cannot be traded away.",
                             [self.b.quotes[q].id for q in no] + ["STK-I2-L77"], "Learner Experience")
            return Check(f"CHK-{p}-access-{key}", "hard", "unverified" if o.service_gaps else "fail",
                         f"No quote in this option provides {label.lower()}.", ["STK-I2-L77"], "Learner Experience")

        out.append(by_feature("hearing_loop", "Hearing loop"))
        out.append(by_feature("live_captions", "Live captions"))
        staff = [q for q, f in feats.items() if f.get("quiet_room_staffing", {}).get("value")]
        quiet = self.cv("N-BRIEF-quiet_space")
        includes = self.cv("N-BRIEF-venue_package_includes") or ""
        if staff and quiet and has_venue and "quiet space" in includes:
            out.append(Check(f"CHK-{p}-access-staffed_quiet_room", "hard", "pass",
                             f"Staffed quiet room: {quiet['room']} in the venue package, staffed by {staff}.",
                             [self.b.quotes[staff[0]].id, "N-BRIEF-quiet_space", "N-BRIEF-venue_package_includes",
                              "STK-I2-L77"], "Learner Experience"))
        elif not staff:
            out.append(Check(f"CHK-{p}-access-staffed_quiet_room", "hard", "unverified" if o.service_gaps else "fail",
                             "No quiet-room staffing in this option.", ["STK-I2-L77"], "Learner Experience"))
        else:
            out.append(self._unverified(f"CHK-{p}-access-staffed_quiet_room", "hard", "Staffed quiet room",
                                        ["N-BRIEF-quiet_space", "N-BRIEF-venue_package_includes"], "Learner Experience"))
        for key, case_claim, spatial in (
                ("wheelchair_seating", "N-BRIEF-wheelchair_spaces", ["N-FP-FP-hall-wheelchair-areas"]),
                ("step_free_access", "N-BRIEF-step_free_route_case",
                 ["N-FP-FP-accessible-elevators-south", "N-FP-FP-accessible-elevator-ev9",
                  "N-FP-FP-accessible-elevator-ev13", "N-FP-FP-accessible-restroom-south"])):
            ids = [case_claim, *spatial]
            if not has_venue:
                out.append(self._unverified(f"CHK-{p}-access-{key}", "hard", key, ids, "Learner Experience"))
            elif self._missing([case_claim]):
                out.append(self._unverified(f"CHK-{p}-access-{key}", "hard", key, [case_claim], "Learner Experience"))
            else:
                spatial_ok = [s for s in spatial if not self._missing([s])]
                limits = self.cv("N-BRIEF-floor_plan_does_not_prove")
                if not spatial_ok:
                    out.append(Check(f"CHK-{p}-access-{key}", "hard", "unverified",
                                     f"{key}: the case record states it, but no floor-plan spatial evidence is "
                                     "available; spatial claims are withheld.", ids + ["STK-I3-L193"], "Learner Experience"))
                else:
                    out.append(Check(f"CHK-{p}-access-{key}", "hard", "pass",
                                     f"{key}: stated by the venue coordination record (case record) and located on the "
                                     f"official floor plan ({len(spatial_ok)} spatial observation(s)). The plan does not "
                                     f"prove {limits or 'operation or configuration'}.",
                                     [case_claim, *spatial_ok, "STK-I3-L193"], "Learner Experience"))
        return out

    def _dietary(self, p, o):
        cats = [q for q in o.quote_ids if self.b.quotes[q].value["category"] == "catering"]
        if not cats:
            return []
        ids = ["N-BRIEF-dietary_response_covers_both_catering_options", "X-dietary-brief-vs-signals"]
        if self._missing(ids):
            return [self._unverified(f"CHK-{p}-dietary", "hard", "Vegetarian and halal meals", ids, "Operations")]
        return [Check(f"CHK-{p}-dietary", "hard", "pass",
                      f"Documented dietary needs are covered by the Operations-coordinated response for {cats} "
                      "(case record); severe-allergy contacts are a separate open prerequisite.",
                      ids + ["STK-I2-L65"], "Operations")]

    def _prerequisites(self, p, o):
        out = []
        for c in self.n.of_kind("prerequisite"):
            applies = c.fields.get("applies_to", [])
            relevant = (any(q in applies for q in o.quote_ids) or "all options" in applies
                        or ("all options using the Plenary Hall" in applies and any(
                            "Plenary Hall" in str(self.b.quotes[q].fields["features"].get("venue_package", {}).get("value", ""))
                            for q in o.quote_ids)))
            if not relevant:
                continue
            if c.support != "supported":
                out.append(self._unverified(f"CHK-{p}-{c.id}", "prerequisite", c.summary, [c.id], c.owner))
                continue
            chk = prerequisite_check(f"CHK-{p}-{c.id}", c.value["name"], c.owner, c.fields["completion_evidence"],
                                     [c.id])
            if c.fields.get("depends_on"):
                chk.summary += f" Depends on {c.fields['depends_on']}."
            out.append(chk)
        return out

    def _budget(self, p, o, cost):
        out = []
        for cat, entry in sorted(cost["categories"].items()):
            b = self.b.get(f"B-budget-{cat}")
            ids = [self.b.quotes[q].id for q in entry["quote_ids"]]
            if b is None:
                out.append(self._unverified(f"CHK-{p}-budget-{cat}", "budget-category", f"Budget check for {cat}",
                                            [f"B-budget-{cat}"] + ids))
                continue
            out.append(category_check(f"CHK-{p}-budget-{cat}", cat, entry["amount_twd"], b["planned_amount_twd"],
                                      b["approval_limit_twd"], b["owner"], [f"B-budget-{cat}"] + ids))
        if cost["incomplete_reason"]:
            out.append(Check(f"CHK-{p}-budget-ceiling", "budget-ceiling", "unverified",
                             f"Total cost cannot be stated: {cost['incomplete_reason']}.",
                             ["B-ceiling", "B-allowances"], "Operations"))
        elif cost["total_with_allowances_twd"] is None or cost["ceiling_twd"] is None:
            out.append(self._unverified(f"CHK-{p}-budget-ceiling", "budget-ceiling", "Planning ceiling",
                                        ["B-ceiling", "B-allowances"], "Operations"))
        else:
            out.append(ceiling_check(f"CHK-{p}-budget-ceiling", cost["total_with_allowances_twd"], cost["ceiling_twd"],
                                     ["B-ceiling", "B-allowances"]))
        if self.b.commitments:
            out.append(Check(f"CHK-{p}-budget-commitments", "budget-category", "unverified",
                             f"Existing commitments {self.b.commitments} are recorded, but no source defines how they "
                             "combine with quotes; no spending-room formula is invented.",
                             [f"B-budget-{k}" for k in self.b.commitments], "Operations"))
        return out
