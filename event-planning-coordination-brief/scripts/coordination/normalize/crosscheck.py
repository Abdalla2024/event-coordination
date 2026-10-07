"""Cross-source consistency checks between normalized claims.

A check whose inputs are all supported is `supported` (consistent) or `conflicting` (inconsistent;
both sides kept, nothing reconciled). A check with any unsupported, conflicting or unresolved input
is `unresolved` and names the missing inputs.
"""

from __future__ import annotations

from datetime import date, datetime

from ..policy import quote_valid_at, tariff_difference_record
from .base import Claim


class Claims:
    def __init__(self, claims: list[Claim]):
        self.by_id = {c.id: c for c in claims}

    def get(self, cid: str) -> Claim | None:
        return self.by_id.get(cid)

    def val(self, cid: str):
        c = self.by_id.get(cid)
        return c.value if c is not None and c.support == "supported" else None

    def of_kind(self, kind: str, supported_only=True) -> list[Claim]:
        return [c for c in self.by_id.values() if c.kind == kind and (c.support == "supported" or not supported_only)]

    def calendar_row(self, role: str) -> Claim | None:
        rid = self.val(f"N-CAL-ROLE-{role}")
        return self.get(f"N-CAL-{rid}") if rid else None


def _check(cid: str, what: str, inputs: list[str], cs: Claims, compare) -> Claim:
    missing = [i for i in inputs if cs.val(i) is None]
    if missing:
        return Claim(cid, "cross-check", f"{what}: cannot be checked; inputs not supported: {missing}.",
                     None, "unresolved", "unverified", [i for i in inputs if cs.get(i)] or ["ASG-TRACE"], [],
                     fields={"inputs": inputs, "missing_inputs": missing})
    consistent, detail = compare(*[cs.val(i) for i in inputs])
    sources = sorted({s for i in inputs for s in cs.get(i).source_ids})
    if consistent:
        return Claim(cid, "cross-check", f"{what}: consistent ({detail}).", {"consistent": True, "detail": detail},
                     "supported", "retrieved", inputs, sources, fields={"inputs": inputs})
    return Claim(cid, "cross-check", f"{what}: INCONSISTENT ({detail}); both sides kept, none chosen.",
                 None, "conflicting", "unverified", inputs, sources,
                 fields={"inputs": inputs, "detail": detail}, owner="Operations")


def _time(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime("%H:%M")


def _same_day(text: str, iso: str) -> bool:
    """'24 October' or '24 October 2026' against an ISO date-time; the year is compared only if stated."""
    d = datetime.fromisoformat(iso)
    parts = text.split()
    if len(parts) == 3 and parts[2] != str(d.year):
        return False
    return parts[:2] == [str(d.day), d.strftime("%B")]


def run(cs: Claims, clock: datetime) -> list[Claim]:
    out: list[Claim] = []
    groups = [f"N-ATT-group-{g}" for g in ("fellows", "partners", "staff", "speakers", "walk_ins")]
    out.append(_check("X-headcount-brief-vs-signals", "Brief planning count vs attendee groups",
                      ["N-BRIEF-planning_people", *groups], cs,
                      lambda brief, *g: (brief == sum(g), f"brief {brief}, groups sum {sum(g)} = {' + '.join(map(str, g))}")))
    out.append(_check("X-dietary-brief-vs-signals", "Brief dietary counts vs attendee signals",
                      ["N-BRIEF-dietary_response_counts", "N-ATT-need-vegetarian_meal", "N-ATT-need-halal_meal",
                       "N-ATT-need-severe_allergy_follow_up"], cs,
                      lambda b, v, h, a: ((b["vegetarian_meal"], b["halal_meal"], b["severe_allergy_follow_up"]) == (v, h, a),
                                          f"brief {b}, signals {v}/{h}/{a}")))

    def row_id(role):
        c = cs.calendar_row(role)
        return c.id if c else f"N-CAL-ROLE-{role}"

    pref, fall, hold = row_id("preferred_event_window"), row_id("fallback_event_window"), row_id("venue_hold")
    key, tear, dead = row_id("keynote_availability"), row_id("teardown_deadline"), row_id("decision_deadline")
    out.append(_check("X-preferred-date", "Brief preferred date vs calendar", ["N-BRIEF-preferred_date", pref], cs,
                      lambda b, c: (b == c["start_at"][:10], f"brief {b}, calendar {c['start_at'][:10]}")))
    out.append(_check("X-fallback-date", "Brief fallback date vs calendar", ["N-BRIEF-fallback_date_text", fall], cs,
                      lambda b, c: (_same_day(b, c["start_at"]), f"brief '{b}' (year not stated), calendar {c['start_at'][:10]}")))
    out.append(_check("X-event-window", "Programme event window vs calendar preferred window",
                      ["N-BRIEF-programme_keynote_and_window", pref], cs,
                      lambda p, c: (p["event_window"] == [_time(c["start_at"]), _time(c["end_at"])],
                                    f"programme {p['event_window']}, calendar {_time(c['start_at'])}–{_time(c['end_at'])}")))
    out.append(_check("X-hard-requirement-times", "Brief opening/completion vs calendar preferred window",
                      ["N-BRIEF-hard_requirements", pref], cs,
                      lambda hr, c: ([i.get("time") for i in hr if i["key"] in ("opening_time", "completion_time")]
                                     == [_time(c["start_at"]), _time(c["end_at"])],
                                     f"brief {[i.get('time') for i in hr if 'time' in i]}, calendar "
                                     f"{_time(c['start_at'])}–{_time(c['end_at'])}")))
    out.append(_check("X-keynote", "Programme keynote vs calendar keynote availability",
                      ["N-BRIEF-programme_keynote_and_window", key], cs,
                      lambda p, c: (p["keynote"] == [_time(c["start_at"]), _time(c["end_at"])],
                                    f"programme {p['keynote']}, calendar {_time(c['start_at'])}–{_time(c['end_at'])}")))
    out.append(_check("X-venue-window", "Venue record coverage vs calendar venue hold", ["N-BRIEF-venue_coverage", hold], cs,
                      lambda v, c: (c["start_at"][:10] in v["dates"] and [v["start"], v["end"]] == [_time(c["start_at"]), _time(c["end_at"])],
                                    f"record {v['dates']} {v['start']}–{v['end']}, hold {c['start_at'][:10]} "
                                    f"{_time(c['start_at'])}–{_time(c['end_at'])}")))
    out.append(_check("X-teardown-window", "Readiness teardown window vs calendar teardown deadline",
                      ["N-BRIEF-readiness_teardown_window", tear], cs,
                      lambda r, c: ([r["start"], r["end"]] == [_time(c["start_at"]), _time(c["end_at"])],
                                    f"readiness {r['start']}–{r['end']}, calendar {_time(c['start_at'])}–{_time(c['end_at'])}")))
    out.append(_check("X-setup-window", "Readiness setup window vs venue hold start and event opening",
                      ["N-BRIEF-readiness_setup_window", hold, pref], cs,
                      lambda r, h, p: ([r["start"], r["end"]] == [_time(h["start_at"]), _time(p["start_at"])],
                                       f"readiness {r['start']}–{r['end']}, hold start {_time(h['start_at'])}, "
                                       f"opening {_time(p['start_at'])}")))
    venue_quotes = [c.id for c in cs.of_kind("vendor-quote") if c.value["category"] == "venue"]
    out.append(_check("X-venue-amount", "Venue record amount vs venue quotes",
                      ["N-BRIEF-venue_package_amount_twd", *(venue_quotes or ["N-QUOTE-venue"])], cs,
                      lambda b, *qs: (all(q["amount_twd"] == b for q in qs),
                                      f"record {b}, quotes {[(q['quote_id'], q['amount_twd']) for q in qs]}")))
    out.append(_check("X-business-clock", "Brief business clock vs run configuration", ["N-BRIEF-business_clock_date"], cs,
                      lambda b: (b == clock.date().isoformat(), f"brief {b}, configured {clock.date().isoformat()}")))
    out.append(_check("X-demo-roster", "Demo roster vs demo count", ["N-BRIEF-demo_roster", "N-BRIEF-demo_count"], cs,
                      lambda r, n: (len(r) == n and len(set(r)) == len(r), f"{len(r)} ids ({len(set(r))} unique), count {n}")))
    out += _references(cs)
    out += _validity(cs, clock, dead, hold)
    out += _tariff(cs, pref)
    return out


def _references(cs: Claims) -> list[Claim]:
    out = []
    quotes = {c.value["quote_id"]: c for c in cs.of_kind("vendor-quote")}
    refs = {}
    for c in cs.of_kind("brief-fact"):
        for q in sorted(set(_quote_ids(c.value))):
            refs.setdefault(q, []).append(c.id)
    for q, cids in sorted(refs.items()):
        if q in quotes:
            out.append(Claim(f"X-brief-quote-{q}", "cross-check", f"Brief reference to {q} matches a vendor quote.",
                             {"consistent": True}, "supported", "retrieved", cids + [quotes[q].id],
                             ["SRC-BRIEF", "SRC-VENDOR"]))
        else:
            out.append(Claim(f"X-brief-quote-{q}", "cross-check",
                             f"Brief refers to {q}, which is not a supported vendor quote; held.",
                             None, "unresolved", "unverified", cids, ["SRC-BRIEF", "SRC-VENDOR"]))
    budget = {c.value["category"]: c for c in cs.of_kind("budget-category")}
    for qid, c in sorted(quotes.items()):
        cat = c.value["category"]
        if budget and cat not in budget:
            out.append(Claim(f"X-quote-category-{qid}", "cross-check",
                             f"{qid} category '{cat}' has no budget category; its budget check is held.",
                             None, "unresolved", "unverified", [c.id], ["SRC-VENDOR", "SRC-BUDGET"]))
    allow = cs.val("N-BRIEF-budget_allowance_categories")
    if allow is not None and budget:
        missing = [a for a in allow if a not in budget]
        out.append(Claim("X-allowance-categories", "cross-check",
                         f"Allowance categories {allow} " + ("exist in the budget." if not missing
                                                              else f"missing from the budget: {missing}."),
                         {"consistent": True, "allowances": allow} if not missing else None,
                         "supported" if not missing else "unresolved", "retrieved" if not missing else "unverified",
                         ["N-BRIEF-budget_allowance_categories"] + [budget[a].id for a in allow if a in budget],
                         ["SRC-BRIEF", "SRC-BUDGET"]))
    return out


def _quote_ids(value) -> list[str]:
    if isinstance(value, str):
        return [value] if value.startswith("Q-") else []
    if isinstance(value, dict):
        return [q for v in value.values() for q in _quote_ids(v)]
    if isinstance(value, list):
        return [q for v in value for q in _quote_ids(v)]
    return []


def _validity(cs: Claims, clock: datetime, dead_id: str, hold_id: str) -> list[Claim]:
    out = []
    deadline = cs.val(dead_id)
    for c in cs.of_kind("vendor-quote"):
        v = c.value
        through = (date.fromisoformat(v["valid_until"]) >= date.fromisoformat(deadline["start_at"][:10])
                   if deadline else None)
        out.append(Claim(f"X-quote-validity-{v['quote_id']}", "quote-validity",
                         f"{v['quote_id']} valid until {v['valid_until']}: "
                         f"{'valid' if quote_valid_at(v['valid_until'], clock) else 'EXPIRED'} at the business clock; "
                         + ("decision deadline unknown" if deadline is None else
                            f"{'covers' if through else 'does NOT cover'} the decision deadline {deadline['start_at'][:10]}"),
                         {"valid_at_business_clock": quote_valid_at(v["valid_until"], clock),
                          "valid_through_decision_deadline": through},
                         "supported", "retrieved" if quote_valid_at(v["valid_until"], clock) else "stale",
                         [c.id] + ([dead_id] if deadline else []), c.source_ids + (["SRC-CALENDAR"] if deadline else [])))
    hold = cs.get(hold_id)
    if hold is not None and hold.support == "supported" and "hold_expires" in hold.fields.get("note_facts", {}) and deadline:
        exp = hold.fields["note_facts"]["hold_expires"]
        after = date.fromisoformat(exp) > date.fromisoformat(deadline["start_at"][:10])
        out.append(Claim("X-hold-vs-deadline", "cross-check",
                         f"Venue hold expires {exp}; decision deadline {deadline['start_at'][:10]} "
                         f"({'hold outlasts the deadline' if after else 'hold expires on or before the deadline'}). "
                         "A hold is not a confirmation.",
                         {"hold_expires": exp, "decision_deadline": deadline["start_at"], "hold_outlasts_deadline": after},
                         "supported", hold.evidence_status, [hold_id, dead_id, "STK-I2-L113"], ["SRC-CALENDAR"]))
    return out


def _tariff(cs: Claims, pref_id: str) -> list[Claim]:
    pref = cs.val(pref_id)
    venue = [c for c in cs.of_kind("vendor-quote") if c.value["category"] == "venue"
             and pref and c.value["available_date"] == pref["start_at"][:10]]
    if not pref or len(venue) != 1:
        return [Claim("X-venue-tariff-difference", "documented-difference",
                      "Venue tariff difference not recorded: the preferred date or a single venue quote for it is not supported.",
                      None, "unresolved", "unverified", [pref_id], ["SRC-VENDOR", "SRC-CALENDAR"],
                      fields={"venue_quotes_on_date": [c.id for c in venue]})]
    q = venue[0]
    weekend = date.fromisoformat(pref["start_at"][:10]).weekday() >= 5
    rate_id = "N-VENUE-official_rate_weekend_twd_per_slot" if weekend else "N-VENUE-official_rate_weekday_twd_per_slot"
    rate = cs.get(rate_id)
    official = {"id": rate_id, "value": rate.value} if rate is not None and rate.support == "supported" else None
    rec = tariff_difference_record("X-venue-tariff-difference", q.value["quote_id"], q.value["amount_twd"],
                                   pref["start_at"][:10], official, [q.id, pref_id])
    return [Claim(rec["id"], "documented-difference", rec["summary"],
                  {k: rec[k] for k in ("planning_value_twd", "official_rate_twd_per_slot", "event_day_kind")},
                  "supported", "retrieved" if official else "unverified", rec["evidence_ids"],
                  ["SRC-VENDOR", "SRC-CALENDAR"] + (["SRC-TICC-HALL"] if official else []),
                  owner=rec["owner"], rationale=rec["rationale"],
                  fields={"planning_value_replaced": False})]
