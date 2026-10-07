"""event-plan.md: the review-ready planning draft.

Three tiers are labelled throughout: **source fact**, **planning state / planner decision**, and
**not established** (unverified, unavailable, conflicting). Values come from the view model; the
renderer formats them and cites the ids they came from.
"""

from __future__ import annotations

from .cite import Citations

SECTIONS = [
    "## 1. Objective and success criteria",
    "## 2. Source and run basis",
    "## 3. Headcount and uncertainty policy",
    "## 4. Timing, run of show and dependencies",
    "## 5. Budget and costs",
    "## 6. Option comparison and feasibility",
    "## 7. Accessibility and safety evidence and limits",
    "## 8. Recommendation or deferral",
    "## 9. Feasible-option shortfall",
    "## 10. Risks",
    "## 11. Unknowns and unresolved items",
    "## 12. Change impacts",
    "## 13. Owners, approvals and review requests",
    "## Appendix: Evidence index",
]
OUTCOME_TEXT = {
    "deferred-to-operations": "No option is recommended. The choice is deferred to Operations.",
    "no-viable-option": "No option is recommended: no option is conditional or feasible on current evidence.",
    "recommended-conditional": "Recommended for Operations review, conditionally",
    "recommended": "Recommended for Operations review",
}


def _twd(v) -> str:
    return "not stated" if v is None else f"TWD {v:,}"


def _hm(iso: str) -> str:
    return iso[11:16]


def banner(view) -> str:
    rec = view["recommendation"]
    feasible = [o["id"] for o in view["options"] if o["feasibility"] == "feasible"]
    conditional = [o["id"] for o in view["options"] if o["feasibility"] == "conditional"]
    lines = [f"> **DRAFT FOR REVIEW — run status `{view['run']['status']}`** "
             f"({'; '.join(view['run']['status_reasons'])}).",
             f"> Feasible options: {len(feasible)}. Conditional options: {len(conditional)}"
             + (f" ({', '.join(conditional)})" if conditional else "") + ".",
             f"> Recommendation outcome: **`{rec['status']}`**. "
             + (OUTCOME_TEXT[rec["status"]] + (f": `{rec['option']}`." if rec["option"] else "")),
             "> Nothing has been booked, approved, committed or confirmed. Every approval is pending."]
    return "\n".join(lines)


def render(view: dict, ri, impact: dict) -> tuple[str, list[str]]:
    ev = Citations(ri)
    f = view["facts"]
    out = [f"# {f['event_name'] or 'Demo Day'} — planning draft", "", banner(view), ""]
    w = view["window"]

    # 1
    out += [SECTIONS[0], "",
            f"- **Event (source fact):** {f['event_name'] or 'not stated'} at {f['venue_name'] or 'not stated'}. "
            + ev("N-BRIEF-event_name", "N-BRIEF-venue_name"),
            f"- **Preferred date (source fact):** {w['date'] if w else 'not established'}, "
            f"{_hm(w['start']) + '–' + _hm(w['end']) if w else ''}. " + ev("B-event-window"),
            f"- **Success criteria (source facts):** at least {f['checkin_target_percent'] or '?'}% of registered "
            "attendees check in; all scheduled fellow demos run; accessibility requests receive a documented "
            "response before the event. " + ev("N-BRIEF-checkin_target_percent", "N-BRIEF-success_all_demos_run",
                                               "N-BRIEF-success_accessibility_response_before_event"), ""]
    # 2
    out += [SECTIONS[1], "",
            f"- Run `{view['run']['run_id']}`, rendered from the run completed at {view['run']['rendered_at']}. "
            f"Business clock {view['run']['business_clock']} (quote and hold validity are judged at this clock). "
            + ev("ASG-CLOCK"),
            "- Unversioned sources are identified by retrieval timestamp; native versions are shown where the "
            "source has one. " + ev("STK-I3-L181"), "",
            "| Source | Status | Retrieved at | Native version |", "|---|---|---|---|"]
    for s in view["sources"]:
        nv = s["native_version"]
        nv_text = ", ".join(f"{k}={v}" for k, v in nv.items()) if isinstance(nv, dict) else "none"
        out.append(f"| `{s['id']}` {s['title']} | {s['status']} | {s['retrieved_at']} | {nv_text} |")
        ev(s["id"])
    out.append("")
    # 3
    hc = view["headcount"]
    out += [SECTIONS[2], ""]
    if hc:
        out += ["**Planning headcount (source facts, separate groups):**", "", "| Group | People |", "|---|---|"]
        out += [f"| {g} | {n} |" for g, n in hc["groups"].items()]
        out += [f"| **Total** | **{hc['total']}** |", "", ev("B-headcount", "STK-I1-L41", "STK-I1-L87"), ""]
    else:
        out += ["**Not established:** the planning headcount could not be built. " + ev("B-headcount"), ""]
    out += ["**Overlapping needs (counted within the groups, never added):**", "", "| Need | Count |", "|---|---|"]
    out += [f"| {k.replace('_', ' ')} | {v} |" for k, v in view["needs"].items()]
    walk = f["walk_ins"]
    out += ["", ev(*[f"B-need-{k}" for k in view["needs"]]), ""]
    if walk and walk["support"] == "supported":
        out += [f"- The walk-in figure ({walk['value']}) is a forecast at **{walk['confidence']}** confidence. "
                + ev(walk["id"])]
    out += ["- **Uncertainty policy:** values are read from the captured sources. Missing, conflicting or "
            "invalid values are held, not guessed. `held` and `available` are planning states, not "
            "confirmations. An option with any open hard dependency is `conditional`, not feasible. "
            + ev("ASG-CHANGED-INPUTS", "STK-I3-L25", "STK-I3-L49", "N-BRIEF-conditional_not_feasible_rule"), ""]
    # 4
    out += [SECTIONS[3], "", "**Calendar facts (source facts; a hold is a planning state, not a booking):**", "",
            "| Item | When | Note |", "|---|---|---|"]
    for key, label, bid in (("window", "Preferred event window", "B-event-window"),
                            ("fallback", "Fallback event window", "B-fallback-window"),
                            ("keynote", "Keynote availability", "B-keynote"),
                            ("hold", "Venue hold (planning state)", "B-venue-hold"),
                            ("teardown", "Teardown window", "B-teardown")):
        v = view[key]
        if v:
            day = v.get("date") or v["start"][:10]
            out.append(f"| {label} | {day} {_hm(v['start'])}–{_hm(v['end'])} | priority {v['priority']} "
                       + ev(bid) + " |")
        else:
            out.append(f"| {label} | not established | " + ev(bid) + " |")
    if view["deadline"]:
        out.append(f"| Plan and budget decision deadline | {view['deadline'][:10]} {_hm(view['deadline'])} | "
                   "decision item, not a calendar event " + ev("B-decision-deadline") + " |")
    for key, label in (("walkthrough", "Accessibility walkthrough"), ("rehearsal", "Rehearsal window")):
        c = view[key]
        if c and c["support"] == "supported":
            out.append(f"| {label} | {c['value']['start_at'][:10]} {_hm(c['value']['start_at'])}–"
                       f"{_hm(c['value']['end_at'])} | owner {c['value']['owner']}, {c['value']['priority']}; "
                       f"{c.get('notes') or ''} " + ev(c["id"]) + " |")
    hv = view["hold_vs_deadline"]
    if hv and hv["support"] == "supported":
        out.append(f"| Venue hold expiry | {hv['value']['hold_expires']} | planning dependency, not an event; "
                   + ev(hv["id"]) + " |")
    prog = view["programme"]
    out += ["", "**Run of show (proposed):**", ""]
    if prog["status"] == "planned":
        out += ["Block durations for the demos, keynote, setup and teardown are **source facts**. Opening, lunch, "
                "break and closing durations, the order and the demo grouping are **Programme planner decisions** "
                "(pending Programme review). Unallocated time is shown as buffer; no activity is invented. "
                + ev("N-BRIEF-planner_schedule_choices", "B-programme"), "",
                "| Time | Block | Basis |", "|---|---|---|"]
        for b in prog["blocks"]:
            basis = {"source": "source fact", "planner-decision": "**planner decision**",
                     "source-duration, planner-placement": "source duration, planner placement",
                     "unallocated": "unallocated Programme buffer"}[b["basis"]]
            out.append(f"| {_hm(b['start'])}–{_hm(b['end'])} | {b['label']} | {basis} " + ev(b["id"]) + " |")
        out += ["", f"Unallocated Programme buffer: {prog['unallocated_minutes']} minutes. All "
                f"{prog['demo_count']} demos are included once.", "", "**Programme planner decisions:**", ""]
        out += [f"- `{d['id']}`: {d['summary']} (owner {d['owner']}; {d['status']}) " + ev(d["id"], *d["evidence_ids"])
                for d in prog["decisions"]]
    else:
        out += [f"**Not established:** the run of show could not be planned ({prog['reason']}). "
                + ev(*prog["evidence_ids"])]
    out += ["", "**Dependencies (no deadline is invented where none is stated):**", "",
            "| Dependency | Outcome | Owner | Affected options |", "|---|---|---|---|"]
    for d in view["dependencies"]:
        out.append(f"| {d['summary']} | {d['outcome']} | {d['owner'] or 'not stated'} | "
                   f"{', '.join(d['affected_options'])} " + ev(d["id"]) + " |")
    out.append("")
    # 5
    out += [SECTIONS[4], "",
            f"- **Planning ceiling (source fact):** {_twd(view['ceiling'])}, including the communications and "
            "contingency allowances. " + ev("B-ceiling", "B-allowances", "STK-I2-L53")]
    if view["allowances"]:
        out.append("- **Allowances (source facts):** " + ", ".join(f"{k} {_twd(v)}" for k, v in view["allowances"].items())
                   + ". " + ev("B-allowances"))
    t = view["tariff"]
    if t:
        out.append(f"- **Venue amount:** {t['summary']} " + ev(t["id"], "STK-I3-L205"))
    out += ["", "| Category | Planned | Approval limit | Owner |", "|---|---|---|---|"]
    out += [f"| {k} | {_twd(v['planned_amount_twd'])} | {_twd(v['approval_limit_twd'])} | {v['owner']} |"
            for k, v in view["budget"].items()]
    out += ["", ev(*[f"B-budget-{k}" for k in view["budget"]]), ""]
    for o in view["candidates"]:
        c = o["costs"]
        out += [f"**{o['id']} ({o['feasibility']})** — category amounts and checks:", "",
                "| Category | Amount | Check |", "|---|---|---|"]
        for chk in o["checks"]:
            if chk["kind"] == "budget-category":
                cat = chk["id"].rsplit("budget-", 1)[1]
                amt = c["categories"].get(cat, {}).get("amount_twd")
                out.append(f"| {cat} | {_twd(amt)} | {chk['outcome']}: {chk['summary']} " + ev(chk["id"]) + " |")
        allow = ", ".join(f"{k} {_twd(v)}" for k, v in (c["allowances_twd"] or {}).items()) or "not stated"
        out += [f"| allowances | {allow} | counted in the ceiling |",
                f"| **Total incl. allowances** | **{_twd(c['total_with_allowances_twd'])}** | remaining under ceiling "
                f"{_twd(c['remaining_under_ceiling_twd'])} " + ev(f"CHK-{o['id']}-budget-ceiling") + " |", ""]
    # 6
    out += [SECTIONS[5], "", "| Option | Status | Total incl. allowances | Reason |", "|---|---|---|---|"]
    for o in view["options"]:
        cost = (_twd(o["costs"]["total_with_allowances_twd"]) if o["costs"]["complete"]
                else f"not stated ({o['costs']['incomplete_reason']})")
        out.append(f"| `{o['id']}` {o['label']} | **{o['feasibility']}** | {cost} | "
                   f"{o['feasibility_reason'].replace('|', '/')} " + ev(o["id"]) + " |")
    out += ["", "**Quotes in the conditional options (planning states; no quote is confirmed):**", "",
            "| Quote | Vendor | Category | Package | Amount | Capacity | Date | Valid until | Planning state |",
            "|---|---|---|---|---|---|---|---|---|"]
    seen = []
    for o in view["candidates"]:
        for q, d in o["quote_details"].items():
            if q in seen:
                continue
            seen.append(q)
            out.append(f"| {q} | {d['vendor']} | {d['category']} | {d['package']} | {_twd(d['amount_twd'])} | "
                       f"{d['capacity']} | {d['available_date']} | {d['valid_until']} | {o['availability'][q]} "
                       + ev(d["evidence_id"]) + " |")
    out.append("")
    # 7
    out += [SECTIONS[6], "", "**Hard accessibility provisions (cannot be traded away):**", "",
            "| Provision | " + " | ".join(f"`{o['id']}`" for o in view["candidates"]) + " |",
            "|---|" + "---|" * len(view["candidates"])]
    for req in (view["accessibility_requirements"] or []):
        cells = []
        for o in view["candidates"]:
            chk = next((c for c in o["checks"] if c["id"] == f"CHK-{o['id']}-access-{req['key']}"), None)
            cells.append(f"{chk['outcome']}: {chk['summary'].replace('|', '/')} " + ev(chk["id"]) if chk else "not checked")
        out.append(f"| {req['key'].replace('_', ' ')} | " + " | ".join(cells) + " |")
    out += ["", ev("B-accessibility-requirements", "STK-I2-L77"), "",
            "**Official 4F floor plan — spatial observations (spatial evidence only):**", ""]
    for c in view["floor_plan"]:
        if c["support"] == "supported":
            out.append(f"- {c['value']} — {c['locator']['value']} " + ev(c["id"]))
        else:
            out.append(f"- **Not established:** {c['summary']} " + ev(c["id"]))
    lim = f["floor_plan_does_not_prove"]
    out += ["", f"- **Limits:** the floor plan does not prove {', '.join(lim) if lim else 'operation or configuration'}; "
            "counts and hearing-loop availability come from the venue coordination record (a case record). "
            + ev("N-BRIEF-floor_plan_does_not_prove", "STK-I3-L193")]
    for r in view["venue_rules"]:
        if r["support"] == "supported":
            out.append(f"- **Official venue rule (source fact):** {r['summary']} " + ev(r["id"]))
    out += ["", "**Dietary and safety:**", ""]
    for o in view["candidates"]:
        chk = next((c for c in o["checks"] if c["id"] == f"CHK-{o['id']}-dietary"), None)
        if chk:
            out.append(f"- `{o['id']}`: {chk['outcome']} — {chk['summary']} " + ev(chk["id"]))
    out += [f"- Severe-allergy follow-up: {view['needs'].get('severe_allergy_follow_up', 'not established')} "
            f"request(s), aggregate only. Named contacts are held by {f['named_contacts_holder'] or 'the owner'} and "
            "are not reproduced here. " + ev("B-need-severe_allergy_follow_up", "N-BRIEF-named_contacts_holder",
                                             "ASG-PRIVACY"), ""]
    # 8
    rec = view["recommendation"]
    out += [SECTIONS[7], "", f"**Outcome: `{rec['status']}`.** "
            + OUTCOME_TEXT[rec["status"]] + (f": `{rec['option']}`." if rec["option"] else "")
            + " " + ev(rec["decision"]["id"]), ""]
    if rec["question"]:
        out += [f"**Question for Operations:** {rec['question']}", ""]
    out += [f"Rationale: {rec['decision']['rationale']}", "",
            "Factors (no weights, no ranking; a preference is stated only when one option dominates):", "",
            "| Factor | Direction | " + " | ".join(f"`{c}`" for c in rec["conditions"]) + " |",
            "|---|---|" + "---|" * len(rec["conditions"])]
    for fac in rec["factors"]:
        out.append(f"| {fac['label']} | {fac['direction']} | "
                   + " | ".join(str(fac["values"].get(c)) for c in rec["conditions"]) + " " + ev(fac["id"]) + " |")
    out += ["", "Stakeholder context (informs the tradeoff; not a weight): "
            + ", ".join(c["id"] for c in rec["context"]) + ". " + ev(*[c["id"] for c in rec["context"]]),
            f"Vendor experience: {view['vendor_experience']['summary'] if view['vendor_experience'] else 'not recorded'} "
            + ev("NOTE-vendor-experience"), "", "Excluded from recommendation:", ""]
    out += [f"- `{e['option_id']}` ({e['feasibility']})" + " " + ev(e["option_id"]) for e in rec["excluded"]]
    out.append("")
    # 9
    short = next((u for u in view["unresolved"] if u["id"] == "UNR-feasible-option-shortfall"), None)
    out += [SECTIONS[8], ""]
    out += [f"{short['summary']} Owner: {short['owner'] or 'not stated'}. " + ev(short["id"], *short["evidence_ids"])
            if short else "No shortfall recorded: the number of feasible options meets the brief's request. "
            + ev("N-BRIEF-requested_feasible_options"), ""]
    # 10
    out += [SECTIONS[9], ""]
    if hv and hv["support"] == "supported":
        out.append(f"- {hv['summary']} " + ev(hv["id"]))
    if walk and walk["support"] == "supported" and walk["confidence"] != "high":
        out.append(f"- The walk-in forecast ({walk['value']}) has {walk['confidence']} confidence; a smaller catering "
                   "buffer may need earlier refreshing if registrations increase. " + ev(walk["id"], "STK-I2-L65"))
    out += ["", "Capacity margins of the conditional options, as recorded by the Phase 3 checks (a margin of 0 "
            "leaves no room for an additional request):", ""]
    for o in view["candidates"]:
        for chk in o["checks"]:
            if chk["id"].startswith(f"CHK-{o['id']}-capacity-"):
                out.append(f"- `{o['id']}` capacity margin — {chk['summary']} " + ev(chk["id"]))
    for q, c in view["quote_validity"].items():
        if c["support"] == "supported" and c["value"].get("valid_through_decision_deadline") is False:
            out.append(f"- {c['summary']} " + ev(c["id"]))
    out.append("")
    # 11
    unknowns = [f"- `{u['id']}`: {u['summary']} (owner {u['owner'] or 'not stated'}) " + ev(u["id"])
                for u in view["unresolved"]]
    unknowns += [f"- **Not established:** `{c['id']}` ({c['support']}): {c['summary']} " + ev(c["id"])
                 for c in view["unsupported_claims"]]
    if prog["status"] != "planned":
        unknowns.append(f"- **Not established:** run of show ({prog['reason']}).")
    if view["vendor_experience"]:
        unknowns.append(f"- {view['vendor_experience']['summary']} " + ev("NOTE-vendor-experience"))
    out += [SECTIONS[10], ""] + (unknowns or ["- None recorded."]) + [""]
    # 12
    out += [SECTIONS[11], "", "If a source changes, these parts of the package must be reconsidered (derived from the "
            "evidence links, not assumed):", "", "| Source | Claims | Options | Deliverable sections |", "|---|---|---|---|"]
    for sid, i in impact.items():
        out.append(f"| `{sid}` | {i['claims']} | {', '.join(i['options']) or 'none'} | {', '.join(i['sections']) or 'none'} |")
    out += ["", ev(*impact.keys()), ""]
    # 13
    out += [SECTIONS[12], "", "| Approval | Owner | Status | Option |", "|---|---|---|---|"]
    for o in view["candidates"]:
        for a in o["approvals"]:
            out.append(f"| {a['summary']} | {a['owner']} | **{a['status']}** | `{o['id']}` " + ev(a["id"]) + " |")
    out += ["", "Approvals for infeasible options are recorded in the decision model but are not requested.", "",
            "**Review requests:** see `draft-communications.md` (all messages are unsent drafts).", ""]
    # appendix
    out += [SECTIONS[13], "", ev.appendix(), ""]
    return "\n".join(out), ev.cited
