"""View model: the only place that reads Phase 3/4 fields for rendering.

It maps and labels existing values and carries their evidence ids. It does no business arithmetic,
feasibility checking, classification or ranking: every number and status shown comes from the
decision model, the recommendation, the programme plan or the validated claims.
"""

from __future__ import annotations

from dataclasses import dataclass

BOOKING_LABEL = {"planning-state-not-confirmed": "planning state, not confirmed",
                 "condition-outstanding": "outstanding condition, not confirmed"}


@dataclass(frozen=True)
class RenderInput:
    run_id: str
    rendered_at: str            # recorded run completion time (UTC); used for DTSTAMP, never the wall clock
    business_clock: str
    sources: list
    claims: list
    decision: dict
    recommendation: dict
    run_status: dict
    programme: dict


def build(ri: RenderInput) -> dict:
    claims = {c["id"]: c for c in ri.claims}
    base = {b["id"]: b for b in ri.decision["baseline"]}
    checks = {c["id"]: c for c in ri.decision["checks"]}
    approvals = {a["id"]: a for a in ri.decision["approvals"]}
    rec = ri.recommendation

    def cv(cid):
        c = claims.get(cid)
        return c["value"] if c and c["support"] == "supported" else None

    def bv(bid):
        b = base.get(bid)
        return b["value"] if b and b["support"] == "supported" else None

    quotes = {c["value"]["quote_id"]: c for c in ri.claims
              if c["kind"] == "vendor-quote" and c["support"] == "supported"}
    factor_of = {f["factor"]: f for f in rec["factors"]}

    options = []
    for o in ri.decision["options"]:
        tradeoffs = []
        if o["id"] in rec["candidates"]:
            for f in rec["factors"]:
                for other, result in f["pairwise"].get(o["id"], {}).items():
                    tradeoffs.append(f"{f['factor']}: {result} than {other} "
                                     f"({f['values'][o['id']]} vs {f['values'][other]})")
        unresolved = [f"{s} [owner: {c['owner'] or 'not stated'}]"
                      for kind in ("open", "unverified") for s, c in
                      ((checks[i]["summary"], checks[i]) for i in _check_ids(o, checks, kind))]
        if o["costs"]["incomplete_reason"]:
            unresolved.append(f"cost not stated: {o['costs']['incomplete_reason']}")
        avail = {}
        for q in o["quote_ids"]:
            c = quotes[q]
            avail[q] = f"{c['value']['status']} ({BOOKING_LABEL[c['booking_state']]})"
        for gap in o["service_gaps"]:
            avail[f"no {gap} quote"] = f"no quote on {o['date']}"
        options.append({
            "id": o["id"], "label": o["label"], "variant": o["variant"], "date": o["date"],
            "feasibility": o["feasibility"], "feasibility_reason": o["rationale"] or "all checks pass",
            "quote_ids": o["quote_ids"], "service_gaps": o["service_gaps"], "costs": o["costs"],
            "availability": avail, "tradeoffs": tradeoffs, "unresolved": unresolved,
            "approval_status": sorted({approvals[a]["status"] for a in o["approval_ids"]}),
            "approvals": [approvals[a] for a in o["approval_ids"]],
            "blocking": o["blocking"], "evidence_ids": o["evidence_ids"],
            "quote_details": {q: {"vendor": quotes[q]["value"]["vendor"], "category": quotes[q]["value"]["category"],
                                  "package": quotes[q]["value"]["package"],
                                  "amount_twd": quotes[q]["value"]["amount_twd"],
                                  "capacity": quotes[q]["value"]["capacity"],
                                  "available_date": quotes[q]["value"]["available_date"],
                                  "valid_until": quotes[q]["value"]["valid_until"],
                                  "status": quotes[q]["value"]["status"],
                                  "confirmation": ("confirmation evidence recorded" if quotes[q]["confirmed"]
                                                   else "not confirmed"),
                                  "evidence_id": quotes[q]["id"]} for q in o["quote_ids"]},
            "checks": [c for c in ri.decision["checks"] if c["option_id"] == o["id"]],
        })

    walk_row = cv("N-CAL-ROLE-accessibility_walkthrough")
    reh_row = cv("N-CAL-ROLE-rehearsal_window")
    return {
        "run": {"run_id": ri.run_id, "rendered_at": ri.rendered_at, "business_clock": ri.business_clock,
                "status": ri.run_status["status"], "status_reasons": ri.run_status["reasons"]},
        "sources": [{"id": s["id"], "title": s["summary"], "status": s["retrieval_status"],
                     "retrieved_at": s["retrieved_at"], "locator": s["locator"],
                     "native_version": (s["version_metadata"] or {}).get("native_version"),
                     "content_hash": s["content_hash"]} for s in ri.sources],
        "facts": {
            "event_name": cv("N-BRIEF-event_name"), "venue_name": cv("N-BRIEF-venue_name"),
            "checkin_target_percent": cv("N-BRIEF-checkin_target_percent"),
            "audience_room": cv("N-BRIEF-audience_room"), "audience_places": cv("N-BRIEF-audience_places"),
            "wheelchair_spaces": cv("N-BRIEF-wheelchair_spaces"), "quiet_space": cv("N-BRIEF-quiet_space"),
            "excluded_room": cv("N-BRIEF-excluded_room"), "floor_plan_does_not_prove": cv("N-BRIEF-floor_plan_does_not_prove"),
            "step_free_route_case": cv("N-BRIEF-step_free_route_case"),
            "named_contacts_holder": cv("N-BRIEF-named_contacts_holder"),
            "requested_feasible_options": cv("N-BRIEF-requested_feasible_options"),
            "walk_ins": claims.get("N-ATT-group-walk_ins"),
        },
        "baseline": base,
        "headcount": bv("B-headcount"),
        "needs": {k.removeprefix("B-need-"): v["value"] for k, v in base.items()
                  if k.startswith("B-need-") and v["support"] == "supported"},
        "window": bv("B-event-window"), "fallback": bv("B-fallback-window"), "keynote": bv("B-keynote"),
        "hold": bv("B-venue-hold"), "teardown": bv("B-teardown"), "deadline": bv("B-decision-deadline"),
        "readiness": bv("B-readiness"), "ceiling": bv("B-ceiling"), "allowances": bv("B-allowances"),
        "budget": {k.removeprefix("B-budget-"): v["value"] for k, v in base.items()
                   if k.startswith("B-budget-") and v["support"] == "supported"},
        "accessibility_requirements": bv("B-accessibility-requirements"),
        "walkthrough": claims.get(f"N-CAL-{walk_row}") if walk_row else None,
        "rehearsal": claims.get(f"N-CAL-{reh_row}") if reh_row else None,
        "hold_vs_deadline": claims.get("X-hold-vs-deadline"),
        "floor_plan": [c for c in ri.claims if c["kind"] == "floor-plan-observation"],
        "venue_rules": [c for c in ri.claims if c["kind"] == "venue-rule"],
        "tariff": next((n for n in ri.decision["notes"] if n["id"] == "NOTE-venue-tariff"), None),
        "vendor_experience": next((n for n in ri.decision["notes"] if n["id"] == "NOTE-vendor-experience"), None),
        "quote_validity": {c["id"].removeprefix("X-quote-validity-"): c for c in ri.claims if c["kind"] == "quote-validity"},
        "options": options,
        "candidates": [o for o in options if o["id"] in rec["candidates"]],
        "recommendation": {"status": rec["status"], "option": rec["recommendation"],
                           "question": rec["question_for_operations"],
                           "judgment_required": rec["operations_judgment_required"],
                           "decision": rec["decision"], "factors": rec["factors"], "factor_of": factor_of,
                           "excluded": rec["excluded"], "conditions": rec["conditions"],
                           "context": rec["stakeholder_context"]},
        "approvals": ri.decision["approvals"],
        "dependencies": ri.decision["dependencies"],
        "unresolved": ri.decision["unresolved"],
        "unsupported_claims": [c for c in ri.claims if c["support"] != "supported"],
        "programme": ri.programme,
        "quotes": quotes,
    }


def _check_ids(option, checks, outcome):
    prefix = f"CHK-{option['id']}-"
    return [cid for cid, c in checks.items() if cid.startswith(prefix) and c["option_id"] == option["id"]
            and c["outcome"] == outcome]
