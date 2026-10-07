"""draft-communications.md: unsent drafts only.

Audiences are roles from the sources or vendor business names from the quotes. No personal names,
addresses, phone numbers or invented deadlines. No message says anything is booked, approved,
committed or confirmed. Vendors are contacted only for quotes in the eligible candidate options.
"""

from __future__ import annotations

from .cite import Citations

SENDER = "Event and Operations Manager (sender; reviews every draft before anything is sent)"


def _twd(v) -> str:
    return "not stated" if v is None else f"TWD {v:,}"


def _msg(n, title, audience, purpose, conditions, owner, basis, body) -> list[str]:
    return [f"## M{n:02d} — {title}", "", "**UNSENT DRAFT**", "",
            f"- **Audience:** {audience}", f"- **Purpose:** {purpose}",
            f"- **Conditions before sending:** {conditions}", f"- **Approval owner:** {owner}",
            f"- **Basis:** {basis}", "", *[f"> {line}" if line else ">" for line in body], ""]


def render(view: dict, ri) -> tuple[str, list[str]]:
    ev = Citations(ri)
    rec = view["recommendation"]
    cands = view["candidates"]
    out = ["# Draft communications", "",
           "> **All messages below are UNSENT DRAFTS.** Nothing has been sent, booked, approved, committed or "
           "confirmed. Run status `" + view["run"]["status"] + "`; recommendation outcome `" + rec["status"] + "`.", ""]
    n = 0

    # Operations review and decision request
    n += 1
    ops_conditions = sorted({c["type"] for cs in rec["conditions"].values() for c in cs
                             if "Operations" in c["owners"]})
    body = ["Please review the attached planning draft (event-plan.md, vendor-comparison.csv, event-calendar.ics).", ""]
    body += [f"- {o['id']}: **{o['feasibility']}**, total {_twd(o['costs']['total_with_allowances_twd'])} including "
             f"allowances." for o in cands] or ["- No option is conditional or feasible on current evidence."]
    body += ["", f"Recommendation outcome: {rec['status']}." + (f" {rec['question']}" if rec["question"] else
                                                               f" Proposed for your review: {rec['option']} (conditional).")]
    short = next((u for u in view["unresolved"] if u["id"] == "UNR-feasible-option-shortfall"), None)
    if short:
        body.append(short["summary"])
    if ops_conditions:
        body += ["", "Open conditions owned by Operations (none is complete yet): " + "; ".join(ops_conditions) + "."]
    hv = view["hold_vs_deadline"]
    if hv and hv["support"] == "supported":
        body.append(f"The venue hold is a planning state, not a booking; it expires {hv['value']['hold_expires']}, "
                    f"and the plan and budget decision deadline is {hv['value']['decision_deadline'][:10]}.")
    body.append("The TICC technical coordination meeting and safety evacuation briefing has no date in any source; "
                "please arrange its timing with the venue.")
    out += _msg(n, "Operations: plan review and decision request", "Operations",
                "Review the draft, make the deferred choice, and act on the open conditions it owns.",
                "Send with the reviewed planning draft.", SENDER,
                ev(rec["decision"]["id"], *(o["id"] for o in cands), "STK-I1-L73", "STK-I3-L157", "STK-I3-L169",
                   *([short["id"]] if short else []), *([hv["id"]] if hv and hv["support"] == "supported" else [])),
                body)

    # Budget owners
    owners: dict[str, list[str]] = {}
    for cat, b in view["budget"].items():
        owners.setdefault(b["owner"], []).append(cat)
    for owner, cats in owners.items():
        n += 1
        body = [f"Please review spending for: {', '.join(cats)}. Approval is pending; nothing is committed.", ""]
        ids = []
        for o in cands:
            body.append(f"{o['id']} ({o['feasibility']}), remaining under the ceiling "
                        f"{_twd(o['costs']['remaining_under_ceiling_twd'])}:")
            for cat in cats:
                chk = next((c for c in o["checks"] if c["id"] == f"CHK-{o['id']}-budget-{cat}"), None)
                if chk:
                    body.append(f"- {chk['summary']}")
                    ids.append(chk["id"])
                elif cat in (o["costs"]["allowances_twd"] or {}):
                    body.append(f"- {cat}: allowance {_twd(o['costs']['allowances_twd'][cat])}, counted in the ceiling.")
            for q, d in o["quote_details"].items():
                if d["category"] in cats and q in view["quote_validity"]:
                    body.append(f"- {view['quote_validity'][q]['summary']}")
                    ids.append(view["quote_validity"][q]["id"])
            ids.append(f"CHK-{o['id']}-budget-ceiling")
        if owner == "Programme" and view["programme"]["status"] == "planned":
            body += ["", "Please also review the run-of-show planner decisions (opening, lunch, break and closing "
                     "durations, order and demo grouping) recorded in the event plan; they are pending your review."]
            ids += [d["id"] for d in view["programme"]["decisions"]]
        out += _msg(n, f"Budget owner {owner}: category spending review", owner,
                    "Category cost, remaining ceiling and cited quote validity for the candidate options.",
                    "Send with the reviewed planning draft.", SENDER,
                    ev(*[f"B-budget-{c}" for c in cats], *ids, "N-BRIEF-budget_owner_review_package"), body)

    # Accessibility walkthrough
    walk = view["walkthrough"]
    if walk and walk["support"] == "supported" and cands:
        n += 1
        v = walk["value"]
        out += _msg(n, "Learner Experience: accessibility walkthrough", v["owner"],
                    "Prepare the accessibility walkthrough that the calendar schedules.",
                    "Send only after venue confirmation is evidenced (the calendar requires it first).",
                    "Operations (venue) and " + v["owner"],
                    ev(walk["id"], "P-accessibility-walkthrough", "P-venue-confirmation"),
                    [f"The calendar schedules the accessibility walkthrough on {v['start_at'][:10]} "
                     f"{v['start_at'][11:16]}–{v['end_at'][11:16]}. It can only proceed after the venue is confirmed; "
                     "the venue is currently held as a planning state, not booked."])

    # Vendors
    quote_ids = sorted({q for o in cands for q in o["quote_ids"]})
    for q in quote_ids:
        d = view["quotes"][q]
        val = d["value"]
        n += 1
        in_opts = [o["id"] for o in cands if q in o["quote_ids"]]
        owner = view["budget"].get(val["category"], {}).get("owner", "not stated")
        body = [f"We are preparing a planning draft for {view['facts']['event_name'] or 'the event'}. Your quote {q} "
                f"({val['package']}, {_twd(val['amount_twd'])}, capacity {val['capacity']}, for {val['available_date']}, "
                f"valid until {val['valid_until']}) is part of {len(in_opts)} option(s) under consideration.",
                "This is not a booking, order, commitment or approval.",
                f"Could you confirm whether the quoted terms and availability for {val['available_date']} still stand?"]
        pre = d.get("prerequisites", {})
        if "named_allergy_contacts" in pre:
            body.append("Your notes say the allergy process requires named contacts. Operations holds those contacts "
                        "and would coordinate them directly; none are included here.")
        if "room_supplied_by_venue" in pre:
            body.append("Your notes say the room itself is supplied by the venue; the venue is not yet confirmed.")
        if val["category"] == "venue" and hv and hv["support"] == "supported":
            body.append(f"We understand the current hold is a planning state that expires {hv['value']['hold_expires']}.")
        route = d.get("facts", {}).get("supply_route", {}).get("value")
        out += _msg(n, f"Vendor {val['vendor']}: confirmation request for {q}",
                    f"{val['vendor']} (quote {q})" + (f", via {route}" if route else ""),
                    "Ask whether the quoted terms and availability still stand. Not a commitment.",
                    f"Send only after Operations approves contacting vendors, and before the quote's stated validity "
                    f"({val['valid_until']}) lapses.",
                    f"Operations and the {val['category']} budget owner ({owner})",
                    ev(d["id"], *in_opts, f"X-quote-validity-{q}", "ASG-DRAFT-ONLY"), body)

    # Attendees
    needs = view["needs"]
    n += 1
    provisions = [r["key"].replace("_", " ") for r in (view["accessibility_requirements"] or [])]
    body = ["Thank you for telling us about your accessibility and dietary needs for the Demo Day.",
            "We have recorded, in aggregate: "
            + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in needs.items()) + ".",
            "Provisions being planned: " + (", ".join(provisions) or "not established") + ".",
            "The date, venue and services are still being planned and are not yet confirmed. A "
            "documented response to each request is planned before the event."]
    out += _msg(n, "Attendees: accessibility and dietary acknowledgement",
                "Registered attendees who submitted accessibility or dietary requests (aggregate message)",
                "Acknowledge requests without promising unconfirmed arrangements.",
                "Send only after Operations approves the wording. Do not add a date or venue as confirmed. "
                "No personal or medical details are included.",
                "Operations and Learner Experience",
                ev(*[f"B-need-{k}" for k in needs], "B-accessibility-requirements",
                   "N-BRIEF-success_accessibility_response_before_event", "ASG-PRIVACY"), body)
    return "\n".join(out), ev.cited
