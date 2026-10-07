"""Deterministic decision rules from references/decision-policy.md.

These functions never decide that something is confirmed, approved or complete. Those states can
only come from evidence ids passed in by the caller (an actual record or human response).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

OUTCOMES = ("pass", "fail", "open", "unverified")
PRECEDENCE = (("fail", "infeasible"), ("unverified", "unverified"), ("open", "conditional"))


@dataclass
class Check:
    id: str
    kind: str            # hard | confirmation | prerequisite | budget-category | budget-ceiling | validity
    outcome: str         # pass | fail | open | unverified
    summary: str
    evidence_ids: list[str] = field(default_factory=list)
    owner: str | None = None

    def __post_init__(self):
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unknown check outcome {self.outcome!r}")

    def as_record(self) -> dict:
        return {"id": self.id, "summary": self.summary, "evidence_ids": self.evidence_ids,
                "owner": self.owner, "rationale": None, "kind": self.kind, "outcome": self.outcome}


def classify(checks: list[Check]) -> tuple[str, dict]:
    """Option feasibility from its checks. Returns (status, reasons-by-outcome)."""
    reasons = {o: [c.id for c in checks if c.outcome == o] for o in OUTCOMES}
    if not checks:
        return "unverified", reasons
    for outcome, status in PRECEDENCE:
        if reasons[outcome]:
            return status, reasons
    return "feasible", reasons


def vendor_status_check(check_id: str, quote_id: str, status: str | None,
                        confirmation_evidence: list[str], source_evidence: list[str],
                        owner: str | None) -> Check:
    """Held/available are planning states; only recorded confirmation evidence closes the check."""
    if confirmation_evidence:
        return Check(check_id, "confirmation", "pass",
                     f"{quote_id}: explicit confirmation recorded.",
                     source_evidence + confirmation_evidence, owner)
    if status in ("held", "available"):
        return Check(check_id, "confirmation", "open",
                     f"{quote_id} is '{status}', a planning state, not a confirmed booking; "
                     "explicit confirmation is required before the option can be feasible.",
                     source_evidence + ["STK-I2-L113", "STK-I3-L25", "STK-I3-L37"], owner)
    if status == "conditional":
        return Check(check_id, "confirmation", "open",
                     f"{quote_id} is 'conditional': an outstanding required condition must be resolved.",
                     source_evidence + ["STK-I2-L101", "STK-I3-L61"], owner)
    return Check(check_id, "confirmation", "unverified",
                 f"{quote_id} status {status!r} has no stakeholder-defined meaning.",
                 source_evidence + ["ASG-CHANGED-INPUTS"], owner)


def prerequisite_check(check_id: str, name: str, owner: str, completion_evidence: list[str],
                       basis: list[str]) -> Check:
    """A required prerequisite stays open until completion evidence exists. No deadline is implied."""
    if completion_evidence:
        return Check(check_id, "prerequisite", "pass", f"{name}: completion evidenced.",
                     basis + completion_evidence, owner)
    return Check(check_id, "prerequisite", "open",
                 f"{name}: required condition with no evidence of completion.",
                 basis + ["STK-I3-L49"], owner)


def category_check(check_id: str, category: str, amount: int, planned: int, limit: int,
                   owner: str, evidence: list[str]) -> Check:
    variance = amount - planned
    note = f"variance from planned {planned}: {variance:+d}" if variance else "equal to planned"
    if amount <= limit:
        return Check(check_id, "budget-category", "pass",
                     f"{category}: {amount} within approval limit {limit} ({note}); "
                     f"ordinary approval by {owner} still pending.",
                     evidence + ["STK-I2-L41"], owner)
    return Check(check_id, "budget-category", "open",
                 f"{category}: {amount} exceeds approval limit {limit} ({note}); "
                 f"explicit approval by {owner} required.",
                 evidence + ["STK-I3-L73", "STK-I1-L221"], owner)


def ceiling_check(check_id: str, total: int, ceiling: int, evidence: list[str]) -> Check:
    if total <= ceiling:
        return Check(check_id, "budget-ceiling", "pass",
                     f"Total {total} including allowances is within the ceiling {ceiling} "
                     f"(remaining {ceiling - total}).", evidence + ["STK-I2-L53"], "Operations")
    return Check(check_id, "budget-ceiling", "fail",
                 f"Total {total} including allowances exceeds the ceiling {ceiling} by {total - ceiling}.",
                 evidence + ["STK-I2-L53"], "Operations")


def quote_valid_at(valid_until: str, clock: datetime) -> bool:
    """A date-only valid_until is treated as valid through the end of that day in the clock's zone [INT]."""
    end = datetime.combine(date.fromisoformat(valid_until) + timedelta(days=1), time(0), tzinfo=clock.tzinfo)
    return clock < end


def approval_record(approval_id: str, subject: str, owner: str, evidence: list[str],
                    response: dict | None = None) -> dict:
    """Approval state. Pending unless a complete actual human response is supplied."""
    required = ("actor", "subject", "plan_revision", "timestamp", "outcome", "reasons")
    status, rationale = "pending", "No human response recorded; the package is a review draft."
    if response is not None:
        missing = [k for k in required if not response.get(k)]
        if missing:
            rationale = f"Response ignored: missing {missing}; stale or partial replies confer no authority."
        elif response["outcome"] not in ("approved", "rejected"):
            rationale = f"Response outcome '{response['outcome']}' recorded; approval remains pending."
        else:
            status, rationale = response["outcome"], f"Recorded human response by {response['actor']}."
    return {"id": approval_id, "summary": subject, "evidence_ids": evidence, "owner": owner,
            "rationale": rationale, "status": status, "response": response}


def tariff_difference_record(record_id: str, quote_id: str, case_amount: int, event_date: str,
                             official_obs: dict | None, evidence: list[str]) -> dict:
    """Document the official published tariff beside the negotiated case amount without replacing it."""
    weekday = date.fromisoformat(event_date).weekday()
    day_kind = "weekend" if weekday >= 5 else "weekday"
    if official_obs is None:
        summary = (f"Planning uses the negotiated case amount TWD {case_amount} ({quote_id}). "
                   "The official published tariff could not be read in this run.")
        official = None
    else:
        official = official_obs.get("value")
        summary = (f"Planning uses the negotiated case amount TWD {case_amount} ({quote_id}, full-day "
                   f"package). The official published {day_kind} rate is TWD {official} per time slot. "
                   "The amounts are not comparable one-for-one and the case amount is not replaced.")
    return {"id": record_id, "summary": summary,
            "evidence_ids": evidence + ["STK-I3-L205"] + ([official_obs["id"]] if official_obs else []),
            "owner": "Operations",
            "rationale": "Stakeholder: continue using the budgeted negotiated figure and note the difference.",
            "planning_value_twd": case_amount, "official_rate_twd_per_slot": official,
            "event_day_kind": day_kind}
