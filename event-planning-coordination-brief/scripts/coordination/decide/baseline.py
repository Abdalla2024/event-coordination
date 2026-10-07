"""Planning baseline built only from normalized claims (never from raw sources).

Each element records the claims it rests on. If any required claim is not `supported`, the element
is `unresolved`, carries no value, and names the blocking claims — so nothing downstream can treat
a conflicting or missing input as settled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

GROUPS = ("fellows", "partners", "staff", "speakers", "walk_ins")
NEEDS = ("wheelchair_seating", "mobility_companion", "live_captions", "hearing_loop", "quiet_room",
         "vegetarian_meal", "halal_meal", "severe_allergy_follow_up")
# Hard accessibility provisions: the brief's list plus the hearing loop the stakeholder added (STK-I2-L77).
ACCESSIBILITY = ("hearing_loop", "step_free_access", "wheelchair_seating", "live_captions", "staffed_quiet_room")


@dataclass
class Element:
    id: str
    summary: str
    value: object
    support: str
    evidence_ids: list[str]
    blocked_by: list[dict] = field(default_factory=list)
    owner: str | None = None

    def as_record(self) -> dict:
        return {"id": self.id, "summary": self.summary, "evidence_ids": self.evidence_ids, "owner": self.owner,
                "rationale": None if not self.blocked_by else "Blocked by claims that are not supported.",
                "kind": "baseline", "support": self.support, "value": self.value, "blocked_by": self.blocked_by}


class Baseline:
    def __init__(self, normalized, clock: datetime):
        self.n = normalized
        self.clock = clock
        self.elements: dict[str, Element] = {}
        self._build()

    # ---- helpers -------------------------------------------------------------------------------
    def claim_value(self, cid):
        c = self.n.get(cid)
        return c.value if c is not None and c.support == "supported" else None

    def blockers(self, cids) -> list[dict]:
        out = []
        for cid in cids:
            c = self.n.get(cid)
            if c is None or c.support != "supported":
                out.append({"claim": cid, "support": c.support if c else "missing",
                            "summary": c.summary if c else "claim not produced"})
        return out

    def add(self, eid, cids, build, summary, owner=None, extra_evidence=()):
        blocked = self.blockers(cids)
        evidence = list(cids) + list(extra_evidence)
        if blocked:
            self.elements[eid] = Element(eid, f"{summary}: unresolved ({', '.join(b['claim'] for b in blocked)} "
                                              "not supported).", None, "unresolved", evidence, blocked, owner)
        else:
            value = build(*[self.claim_value(c) for c in cids])
            self.elements[eid] = Element(eid, f"{summary}: {value}", value, "supported", evidence, [], owner)

    def get(self, eid):
        e = self.elements.get(eid)
        return e.value if e is not None and e.support == "supported" else None

    def calendar_row_id(self, role):
        rid = self.claim_value(f"N-CAL-ROLE-{role}")
        return f"N-CAL-{rid}" if rid else f"N-CAL-ROLE-{role}"

    # ---- elements ------------------------------------------------------------------------------
    def _build(self):
        groups = [f"N-ATT-group-{g}" for g in GROUPS]
        self.add("B-headcount", groups,
                 lambda *v: {"total": sum(v), "groups": dict(zip(GROUPS, v)),
                             "basis": "sum of separate groups; overlapping needs not added"},
                 "Planning headcount", extra_evidence=["STK-I1-L41", "STK-I1-L87", "X-headcount-brief-vs-signals"])
        for need in NEEDS:
            self.add(f"B-need-{need}", [f"N-ATT-need-{need}"], lambda v: v, f"Need {need} (overlapping)")

        win = self.calendar_row_id("preferred_event_window")
        self.add("B-event-window", [win], lambda r: {"date": r["start_at"][:10], "start": r["start_at"],
                                                     "end": r["end_at"], "priority": r["priority"]},
                 "Preferred event window")
        fall = self.calendar_row_id("fallback_event_window")
        self.add("B-fallback-window", [fall], lambda r: {"date": r["start_at"][:10], "start": r["start_at"],
                                                        "end": r["end_at"], "priority": r["priority"]},
                 "Fallback event window")
        key = self.calendar_row_id("keynote_availability")
        self.add("B-keynote", [key], lambda r: {"date": r["start_at"][:10], "start": r["start_at"], "end": r["end_at"],
                                               "priority": r["priority"], "owner": r["owner"]},
                 "Keynote availability", extra_evidence=["N-BRIEF-programme_keynote_and_window"])
        hold = self.calendar_row_id("venue_hold")
        self.add("B-venue-hold", [hold], lambda r: {"date": r["start_at"][:10], "start": r["start_at"],
                                                   "end": r["end_at"], "priority": r["priority"]},
                 "Venue hold window (a hold is not a confirmation)", extra_evidence=["STK-I2-L113"])
        tear = self.calendar_row_id("teardown_deadline")
        self.add("B-teardown", [tear], lambda r: {"start": r["start_at"], "end": r["end_at"], "priority": r["priority"]},
                 "Teardown window", extra_evidence=["STK-I1-L249"])
        dead = self.calendar_row_id("decision_deadline")
        self.add("B-decision-deadline", [dead], lambda r: r["start_at"], "Plan and budget decision deadline")
        self.add("B-venue-coverage", ["N-BRIEF-venue_coverage"], lambda v: v, "Venue coordination record coverage")
        self.add("B-readiness", ["N-BRIEF-readiness_base_bundles", "N-BRIEF-readiness_date",
                                 "N-BRIEF-readiness_setup_window", "N-BRIEF-readiness_teardown_window"],
                 lambda b, d, s, t: {"date": d, "catering_alternatives": b["catering_alternatives"],
                                     "common": b["common"], "setup": s, "teardown": t},
                 "Readiness confirmation (case record)")
        self.add("B-time-requirements", ["N-BRIEF-hard_requirements"],
                 lambda hr: {i["key"]: i["time"] for i in hr if "time" in i}, "Opening and completion times")

        self.add("B-ceiling", ["N-BRIEF-planning_ceiling_twd"], lambda v: v, "Planning ceiling TWD",
                 owner="Operations")
        budget = [c for c in self.n.of_kind("budget-category")]
        for c in budget:
            if c.support == "supported":
                cat = c.value["category"]
                self.add(f"B-budget-{cat}", [c.id], lambda v: v, f"Budget {cat}", owner=c.value["owner"])
        self.add("B-allowances", ["N-BRIEF-budget_allowance_categories", "X-allowance-categories"],
                 lambda cats, _x: {cat: self.get(f"B-budget-{cat}")["planned_amount_twd"] for cat in cats},
                 "Budget allowances counted in the ceiling", extra_evidence=["STK-I2-L53"])
        committed = {c.value["category"]: c.value["committed_amount_twd"] for c in budget if c.support == "supported"}
        self.commitments = {k: v for k, v in committed.items() if v}

        brief_req = self.claim_value("N-BRIEF-hard_requirements") or []
        brief_keys = {i["key"] for i in brief_req}
        self.add("B-accessibility-requirements", ["N-BRIEF-hard_requirements"],
                 lambda _hr: [{"key": k, "basis": (["N-BRIEF-hard_requirements"] if k in brief_keys else [])
                               + (["STK-I2-L77"] if k in ("hearing_loop", "step_free_access", "wheelchair_seating",
                                                          "live_captions", "staffed_quiet_room") else [])}
                              for k in ACCESSIBILITY],
                 "Hard accessibility provisions (cannot be traded away)", extra_evidence=["STK-I2-L77"])
        self.add("B-programme", ["N-BRIEF-demo_count", "N-BRIEF-demo_roster", "N-BRIEF-demo_presentation_minutes",
                                 "N-BRIEF-demo_changeover_minutes", "N-BRIEF-programme_keynote_and_window"],
                 lambda n, r, p, c, k: {"demo_count": n, "roster": r, "presentation_minutes": p,
                                        "changeover_minutes": c, "keynote": k["keynote"], "event_window": k["event_window"]},
                 "Programme inputs", extra_evidence=["X-demo-roster"])
        self.quotes = {c.value["quote_id"]: c for c in self.n.of_kind("vendor-quote") if c.support == "supported"}

    def records(self) -> list[dict]:
        return [e.as_record() for e in self.elements.values()]
