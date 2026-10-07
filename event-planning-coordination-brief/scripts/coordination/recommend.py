"""Recommendation layer: compares non-infeasible options from the Phase 3 decision model.

Read-only over the decision model: it never changes option statuses, costs, checks or approvals.
A preference is stated only by dominance across the evidenced factors below. There are no weights,
scores or ranking formula (STK-I3-L85, STK-I3-L97). When the factors favour different candidates,
the result is `deferred-to-operations` and names the tradeoff Operations must resolve.
"""

from __future__ import annotations

from dataclasses import dataclass

ELIGIBLE = ("conditional", "feasible")
STAKEHOLDER_CONTEXT = ("STK-I2-L65", "STK-I1-L111", "STK-I3-L85", "STK-I3-L97", "STK-I3-L121")

# factor -> (label used in tradeoff statements, direction)
FACTORS = {
    "cost": ("lower cost and greater budget headroom", "lower total is better"),
    "catering_buffer": ("the larger catering capacity buffer", "larger buffer is better"),
    "open_conditions": ("fewer open condition types", "fewer normalized condition types is better"),
    "unverified_checks": ("fewer unverified checks", "fewer is better"),
    "quote_validity": ("all quotes valid through the decision deadline", "all valid is better than not all valid"),
}


@dataclass
class Recommendation:
    status: str
    recommendation: str | None
    candidates: list[str]
    excluded: list[dict]
    factors: list[dict]
    tradeoffs: list[dict]
    decision: dict
    operations_judgment_required: bool
    question_for_operations: str | None
    stakeholder_context: list[dict]
    conditions: dict
    carried_dependencies: list[dict]
    carried_unresolved: list[dict]

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


# ---- normalized condition types ----------------------------------------------------------------

def condition_types(option: dict, checks: list[dict], quotes: dict) -> dict[str, dict]:
    """Open checks of one option -> {condition type: {owners, check_ids, summaries}}.

    Types are compared instead of check ids or prose, so the same underlying condition counts once:
    a held/available confirmation is typed by service category, a quote's own outstanding condition is
    folded into the named prerequisites for that quote, and an above-limit category is one approval type.
    """
    raw: dict[str, dict] = {}
    prefix = f"CHK-{option['id']}-"
    for c in checks:
        if c["option_id"] != option["id"] or c["outcome"] != "open":
            continue
        suffix = c["id"].removeprefix(prefix)
        if suffix.startswith("P-"):
            ctype = suffix
        elif suffix.endswith("-confirmation") and suffix.removesuffix("-confirmation") in quotes:
            q = suffix.removesuffix("-confirmation")
            v = quotes[q]
            ctype = f"confirmation:{v['category']}" if v["status"] in ("held", "available") else f"quote-condition:{q}"
        elif suffix == "readiness":
            named = [q for q in option["quote_ids"] if q in c["summary"]]
            ctype = f"quote-condition:{named[0]}" if named else "readiness"
        elif suffix.startswith("budget-"):
            ctype = f"explicit-approval:{suffix.removeprefix('budget-')}"
        else:
            ctype = suffix
        entry = raw.setdefault(ctype, {"owners": [], "check_ids": [], "summaries": []})
        if c["owner"] and c["owner"] not in entry["owners"]:
            entry["owners"].append(c["owner"])
        entry["check_ids"].append(c["id"])
        entry["summaries"].append(c["summary"])
    # a quote's outstanding condition is the same thing as its named prerequisites: count it once
    for ctype in [t for t in raw if t.startswith("quote-condition:")]:
        q = ctype.split(":", 1)[1]
        named = [t for t in raw if t.startswith("P-") and t.endswith(f"-{q}")]
        if named:
            raw[named[0]]["check_ids"] += raw[ctype]["check_ids"]
            raw[named[0]]["summaries"] += raw[ctype]["summaries"]
            del raw[ctype]
    return dict(sorted(raw.items()))


# ---- factor values and pairwise comparison -------------------------------------------------------

def _factor_values(option, cmp, ctypes, normalized) -> dict:
    cost = option["costs"]
    validity = []
    for q in option["quote_ids"]:
        claim = normalized.get(f"X-quote-validity-{q}")
        validity.append(claim.value.get("valid_through_decision_deadline")
                        if claim is not None and claim.support == "supported" else None)
    return {
        "cost": {"value": cost["total_with_allowances_twd"],
                 "detail": {"total_with_allowances_twd": cost["total_with_allowances_twd"],
                            "remaining_under_ceiling_twd": cost["remaining_under_ceiling_twd"]},
                 "evidence_ids": [f"CHK-{option['id']}-budget-ceiling"]},
        "catering_buffer": {"value": cmp.get("catering_buffer_people"),
                            "detail": {"limitation": "the register does not define who the quoted capacity covers "
                                                     "(STK-I3-L133)"},
                            "evidence_ids": [c for c in cmp["evidence_ids"] if "capacity-catering" in c] + ["STK-I3-L133"]},
        "open_conditions": {"value": len(ctypes), "detail": {"types": list(ctypes)},
                            "evidence_ids": [i for t in ctypes.values() for i in t["check_ids"]] or [cmp["id"]]},
        "unverified_checks": {"value": len(cmp.get("unverified_checks", [])), "detail": {},
                              "evidence_ids": [cmp["id"]]},
        "quote_validity": {"value": None if None in validity else all(validity),
                           "detail": {"per_quote": dict(zip(option["quote_ids"], validity))},
                           "evidence_ids": [f"X-quote-validity-{q}" for q in option["quote_ids"]]},
    }


def _pair(factor, a, b) -> str:
    if a is None or b is None:
        return "not-comparable"
    if a == b:
        return "tie"
    if factor == "quote_validity":
        return "better" if a and not b else "worse"
    if factor == "catering_buffer":
        return "better" if a > b else "worse"
    return "better" if a < b else "worse"          # cost, open_conditions, unverified_checks: lower is better


# ---- main ---------------------------------------------------------------------------------------

def recommend(model, normalized) -> Recommendation:
    options = {o["id"]: o for o in model.options}
    cmps = {c["option_id"]: c for c in model.comparison}
    quotes = {q: c.value for q, c in model.baseline.quotes.items()}
    candidates = [o["id"] for o in model.options if o["feasibility"] in ELIGIBLE]
    excluded = [{"option_id": o["id"], "feasibility": o["feasibility"],
                 "reason": o["rationale"] or o["feasibility"], "evidence_ids": [o["id"]]}
                for o in model.options if o["feasibility"] not in ELIGIBLE]
    ctypes = {oid: condition_types(options[oid], model.checks, quotes) for oid in candidates}
    values = {oid: _factor_values(options[oid], cmps[oid], ctypes[oid], normalized) for oid in candidates}

    factors = []
    for f, (label, direction) in FACTORS.items():
        pairwise = {a: {b: _pair(f, values[a][f]["value"], values[b][f]["value"]) for b in candidates if b != a}
                    for a in candidates}
        factors.append({
            "id": f"TO-{f}", "factor": f, "label": label, "direction": direction,
            "summary": f"{label}: " + ", ".join(f"{oid} = {values[oid][f]['value']}" for oid in candidates),
            "values": {oid: values[oid][f]["value"] for oid in candidates},
            "details": {oid: values[oid][f]["detail"] for oid in candidates},
            "pairwise": pairwise,
            "evidence_ids": sorted({e for oid in candidates for e in values[oid][f]["evidence_ids"]}),
            "owner": None, "rationale": None,
        })

    conditions = {oid: [{"type": t, "owners": v["owners"], "check_ids": v["check_ids"]}
                        for t, v in ctypes[oid].items()] for oid in candidates}
    context = _context(normalized)
    deps, unres = list(model.dependencies), list(model.unresolved)

    if not candidates:
        return Recommendation(
            "no-viable-option", None, [], excluded, factors, [],
            _decision("no-viable-option", None, "No option is conditional or feasible on current evidence.",
                      ["No candidate remains; see the excluded options and unresolved items."],
                      [e["option_id"] for e in excluded] or [u["id"] for u in unres] or ["ASG-NO-INVENT"]),
            True, "No option can currently be recommended. Operations must resolve the blocking items listed.",
            context, conditions, deps, unres)

    dominant = [a for a in candidates if _dominates(a, candidates, factors)]
    if len(candidates) == 1:
        winner, sole = candidates[0], True
    elif len(dominant) == 1:
        winner, sole = dominant[0], False
    else:
        winner, sole = None, False

    if winner is None:
        favoured = _favoured(candidates, factors)
        blocked = [f["factor"] for f in factors if any(r == "not-comparable" for p in f["pairwise"].values()
                                                       for r in p.values())]
        parts = [f"{FACTORS[f][0]} ({', '.join(oids)})" for f, oids in favoured.items()]
        statements = [f"{f['label']} favours {', '.join(favoured[f['factor']])}: {f['summary']}"
                      for f in factors if f["factor"] in favoured]
        statements += [f"{FACTORS[b][0]}: not comparable (a value is missing or unsupported), so no dominance "
                       "can be claimed." for b in blocked]
        question = ("Operations judgment required: choose between " + " and ".join(parts) + "."
                    if len(parts) > 1 else
                    "Operations judgment required: the evidence does not establish that one candidate is at least "
                    "as good on every factor" + (f" ({', '.join(blocked)} not comparable)." if blocked else "."))
        return Recommendation(
            "deferred-to-operations", None, candidates, excluded, factors, _separating(factors),
            _decision("deferred-to-operations", None,
                      "No candidate dominates on the evidenced factors, and the stakeholder gave no fixed ordering "
                      "of these tradeoffs; the choice is left to Operations.",
                      statements or ["No factor separates the candidates."],
                      [f["id"] for f in factors] + list(STAKEHOLDER_CONTEXT)),
            True, question, context, conditions, deps, unres)

    status = "recommended" if options[winner]["feasibility"] == "feasible" else "recommended-conditional"
    open_list = conditions[winner]
    why = ("It is the only recommendable option." if sole else
           "It is at least as good as every other candidate on every factor and better on at least one.")
    if status == "recommended-conditional":
        why += " It remains conditional on: " + "; ".join(
            f"{c['type']} (owner {', '.join(c['owners']) or 'not stated'})" for c in open_list) + "."
    ties = [f"{f['label']}: {f['summary']}" for f in factors]
    return Recommendation(
        status, winner, candidates, excluded, factors, _separating(factors),
        _decision(status, winner, why, ties, [winner] + [f["id"] for f in factors]),
        False, None, context, conditions, deps, unres)


def _separating(factors) -> list[dict]:
    """Factor records on which candidates differ: the tradeoffs a reviewer needs to see."""
    return [f for f in factors if any(r in ("better", "worse") for p in f["pairwise"].values() for r in p.values())]


def _dominates(a, candidates, factors) -> bool:
    for b in candidates:
        if b == a:
            continue
        results = [f["pairwise"][a][b] for f in factors]
        if "not-comparable" in results or "worse" in results or "better" not in results:
            return False
    return True


def _favoured(candidates, factors) -> dict[str, list[str]]:
    """Factors on which some candidate is strictly best (better than or tied with all, better than one)."""
    out = {}
    for f in factors:
        best = [a for a in candidates
                if all(f["pairwise"][a][b] in ("better", "tie") for b in candidates if b != a)
                and any(f["pairwise"][a][b] == "better" for b in candidates if b != a)]
        if best:
            out[f["factor"]] = best
    return out


def _decision(status, option, rationale, tradeoffs, evidence) -> dict:
    return {"id": "DEC-recommendation", "summary": f"Recommendation outcome: {status}"
            + (f" ({option})" if option else ""), "evidence_ids": list(dict.fromkeys(evidence)),
            "owner": "Operations", "rationale": rationale, "tradeoffs": tradeoffs, "status": status,
            "recommendation": option, "approval_status": "pending"}


def _context(normalized) -> list[dict]:
    out = [{"id": f"CTX-{sid}", "summary": f"Stakeholder context {sid}; informs the tradeoff statement, not a weight.",
            "evidence_ids": [sid], "owner": None, "rationale": None} for sid in STAKEHOLDER_CONTEXT]
    walk = normalized.get("N-ATT-group-walk_ins")
    if walk is not None and walk.support == "supported":
        out.append({"id": "CTX-walk-in-forecast",
                    "summary": f"Walk-in forecast {walk.value} people at {walk.fields['confidence']} confidence; "
                               "relevant to the catering buffer tradeoff (STK-I2-L65).",
                    "evidence_ids": [walk.id, "STK-I2-L65"], "owner": None, "rationale": None})
    return out


# ---- run status ---------------------------------------------------------------------------------

def run_status(source_records: list[dict], model, rec: Recommendation) -> dict:
    """Execution outcome kept separate from the business decision.

    complete: analysis done and a justified recommendation produced.
    partial: analysis done, but a required business decision is unresolved or needs human judgment,
             or a source was not retrieved.
    blocked: a required prerequisite stopped the analysis (no options could be built).
    failed is reserved for the workflow itself failing; it is never produced here.
    """
    reasons = []
    not_retrieved = [s["id"] for s in source_records if s["retrieval_status"] != "retrieved"]
    if not model.options:
        return {"status": "blocked", "reasons": ["no candidate options could be generated"]
                + [u["summary"] for u in model.unresolved if u["id"].startswith("GEN-")],
                "decision_status": rec.status}
    if not_retrieved:
        reasons.append(f"sources not retrieved: {not_retrieved}")
    if rec.status in ("deferred-to-operations", "no-viable-option"):
        reasons.append(f"recommendation outcome '{rec.status}' requires Operations judgment")
    return {"status": "partial" if reasons else "complete",
            "reasons": reasons or ["analysis complete with a justified recommendation; approvals remain pending"],
            "decision_status": rec.status}
