"""Decision and feasibility layer: normalized claims -> baseline, candidate options, checks, classification.

Deterministic. It classifies and compares; it does not rank or recommend. The recommendation is a
separate layer, `coordination.recommend` (STK-I3-L85, STK-I3-L97), that reads this model unchanged.
Read-only: it never books, pays, invites, commits, writes calendars or changes approvals.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from ..policy import approval_record, classify
from .baseline import Baseline
from .checks import Evaluator
from .options import generate


@dataclass
class DecisionModel:
    baseline: Baseline
    options: list[dict]
    checks: list[dict]
    approvals: list[dict]
    dependencies: list[dict]
    unresolved: list[dict]
    comparison: list[dict]
    notes: list[dict]

    def option(self, oid: str) -> dict | None:
        return next((o for o in self.options if o["id"] == oid), None)

    def summary(self) -> dict:
        return {"options": {o["id"]: o["feasibility"] for o in self.options},
                "by_feasibility": dict(Counter(o["feasibility"] for o in self.options)),
                "checks": dict(Counter(c["outcome"] for c in self.checks)),
                "dependencies": len(self.dependencies), "unresolved": len(self.unresolved)}

    def as_dict(self) -> dict:
        return {"baseline": self.baseline.records(), "options": self.options, "checks": self.checks,
                "approvals": self.approvals, "dependencies": self.dependencies, "unresolved": self.unresolved,
                "comparison": self.comparison, "notes": self.notes, "recommendation": None,
                "recommendation_status": "not made here; see the recommendation layer (coordination.recommend)"}


def decide(normalized, clock: datetime) -> DecisionModel:
    baseline = Baseline(normalized, clock)
    ev = Evaluator(normalized, baseline)
    candidates, gen_issues = generate(baseline)
    options, all_checks, approvals, comparison = [], [], [], []
    deps: dict[str, dict] = {}
    for o in candidates:
        checks, cost = ev.evaluate(o)
        status, reasons = classify(checks)
        recs = [dict(c.as_record(), option_id=o.id, rationale=None if c.outcome == "pass" else c.summary)
                for c in checks]
        all_checks += recs
        by_id = {c.id: c for c in checks}
        appr = _approvals(o, cost, baseline, by_id)
        approvals += appr
        for c in checks:
            if c.outcome in ("open", "unverified"):
                key = "DEP-" + c.id.removeprefix(f"CHK-{o.id}-")
                d = deps.setdefault(key, {"id": key, "summary": c.summary, "evidence_ids": [], "owner": c.owner,
                                          "rationale": None, "kind": c.kind, "outcome": c.outcome,
                                          "affected_options": [], "deadline": None})
                d["affected_options"].append(o.id)
                d["evidence_ids"] = list(dict.fromkeys(d["evidence_ids"] + [c.id]))
        blocking = {k: [by_id[i].summary for i in v] for k, v in reasons.items() if k != "pass" and v}
        options.append({
            "id": o.id, "summary": f"{o.label}: {status}", "evidence_ids": [c.id for c in checks] + o.derived_from,
            "owner": "Operations",
            "rationale": None if status == "feasible" else _why(status, reasons, by_id),
            "feasibility": status, "label": o.label, "variant": o.variant, "date": o.date,
            "quote_ids": o.quote_ids, "service_gaps": o.service_gaps, "costs": cost,
            "check_counts": {k: len(v) for k, v in reasons.items()}, "blocking": blocking,
            "approval_ids": [a["id"] for a in appr],
        })
        if status != "infeasible":
            comparison.append(_compare(o, status, cost, checks, baseline))

    unresolved = list(gen_issues) + [
        {"id": f"UNR-{e.id}", "summary": e.summary, "evidence_ids": [e.id], "owner": e.owner, "rationale": None,
         "blocked_by": e.blocked_by} for e in baseline.elements.values() if e.support != "supported"]
    feasible = [o for o in options if o["feasibility"] == "feasible"]
    requested = baseline.claim_value("N-BRIEF-requested_feasible_options")
    if requested is not None and len(feasible) < requested:
        unresolved.append({
            "id": "UNR-feasible-option-shortfall",
            "summary": f"The brief asks for {requested} feasible options; {len(feasible)} are feasible on current "
                       "evidence. No option is upgraded and none is fabricated.",
            "evidence_ids": ["N-BRIEF-requested_feasible_options", "N-BRIEF-no_fabricated_second_option",
                             "N-BRIEF-conditional_not_feasible_rule", "ASG-NO-INVENT"],
            "owner": baseline.claim_value("N-BRIEF-plan_approver"), "rationale": None,
            "feasible_options": [o["id"] for o in feasible]})
    notes = [{
        "id": "NOTE-vendor-experience",
        "summary": "Vendor experience / familiar-supplier status is not evidenced by any disclosed source; it is "
                   "noted qualitatively and not scored.",
        "evidence_ids": ["STK-I3-L109", "STK-I3-L121", "STK-I2-L89"], "owner": None, "rationale": None,
        "support": "unresolved"}]
    tariff = normalized.get("X-venue-tariff-difference")
    if tariff is not None:
        notes.append({"id": "NOTE-venue-tariff", "summary": tariff.summary, "evidence_ids": [tariff.id],
                      "owner": tariff.owner, "rationale": tariff.rationale, "support": tariff.support,
                      "planning_value_replaced": False})
    return DecisionModel(baseline, options, all_checks, approvals, list(deps.values()), unresolved, comparison, notes)


def _why(status, reasons, by_id) -> str:
    key = {"infeasible": "fail", "unverified": "unverified", "conditional": "open"}[status]
    return f"{status}: " + " | ".join(by_id[i].summary for i in reasons[key])


def _approvals(o, cost, baseline, by_id) -> list[dict]:
    out = [approval_record(f"APR-{o.id}-operations-plan", f"Operations approval of plan, date {o.date} and venue",
                           "Operations", ["N-BRIEF-plan_approver", "STK-I1-L73"])]
    cats = dict(cost["categories"])
    for cat, amt in (cost["allowances_twd"] or {}).items():
        cats.setdefault(cat, {"amount_twd": amt, "quote_ids": [], "allowance": True})
    for cat, entry in sorted(cats.items()):
        b = baseline.get(f"B-budget-{cat}")
        if b is None:
            continue
        chk = by_id.get(f"CHK-{o.id}-budget-{cat}")
        explicit = chk is not None and chk.outcome == "open"
        rec = approval_record(f"APR-{o.id}-budget-{cat}",
                              f"{'Explicit' if explicit else 'Ordinary'} approval of {cat} spending TWD "
                              f"{entry['amount_twd']} by {b['owner']}", b["owner"],
                              [f"B-budget-{cat}"] + ([chk.id] if chk else []) +
                              (["STK-I3-L73"] if explicit else ["STK-I2-L41"]))
        rec.update({"category": cat, "amount_twd": entry["amount_twd"], "explicit_required": explicit,
                    "allowance": entry.get("allowance", False)})
        out.append(rec)
    return out


def _compare(o, status, cost, checks, baseline) -> dict:
    """Deterministic comparison facts for the recommendation layer. No weights, no ranking (STK-I3-L85)."""
    head = baseline.get("B-headcount")
    cat_cap = [baseline.quotes[q].value["capacity"] for q in o.quote_ids
               if baseline.quotes[q].value["category"] == "catering"]
    variances = {}
    for cat, entry in cost["categories"].items():
        b = baseline.get(f"B-budget-{cat}")
        if b and entry["amount_twd"] != b["planned_amount_twd"]:
            variances[cat] = entry["amount_twd"] - b["planned_amount_twd"]
    return {
        "id": f"CMP-{o.id}", "summary": f"Comparison facts for {o.id} ({status})",
        "evidence_ids": [c.id for c in checks if c.kind in ("budget-category", "budget-ceiling")
                         or c.id.startswith(f"CHK-{o.id}-capacity-catering")],
        "owner": None, "rationale": None, "option_id": o.id, "feasibility": status,
        "total_with_allowances_twd": cost["total_with_allowances_twd"],
        "remaining_under_ceiling_twd": cost["remaining_under_ceiling_twd"],
        "catering_buffer_people": (cat_cap[0] - head["total"]) if (cat_cap and head) else None,
        "category_variances_twd": variances,
        "categories_above_approval_limit": [c.id.rsplit("-", 1)[-1] for c in checks
                                            if c.kind == "budget-category" and c.outcome == "open"],
        "open_conditions": [c.summary for c in checks if c.outcome == "open"],
        "unverified_checks": [c.summary for c in checks if c.outcome == "unverified"],
        "vendor_experience": "not evidenced; not scored",
    }
