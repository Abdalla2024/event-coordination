"""Run-of-show planning: a non-overlapping programme from evidenced times plus Programme planner decisions.

Source facts: the event window, keynote time, setup and teardown windows, the demo roster and the
10 + 3 minute demo durations (Phase 3 baseline). Planner decisions: opening, lunch, break and closing
durations, ordering and grouping (`references/programme-decisions.json`, owned by Programme, pending
review). The brief delegates these choices to the planner (N-BRIEF-planner_schedule_choices).
Gaps are shown as unallocated Programme buffer; no activity is invented to fill them.

This is a planning layer: it does time arithmetic. It reads the Phase 3 decision model as data and
never changes it.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from .config import REFERENCES_DIR

REQUIRED_BASELINE = ("B-event-window", "B-keynote", "B-programme", "B-readiness", "B-teardown")
SOURCE, PLANNER, MIXED, UNALLOCATED = "source", "planner-decision", "source-duration, planner-placement", "unallocated"


def load_decisions(path: Path | None = None) -> dict:
    return json.loads((path or REFERENCES_DIR / "programme-decisions.json").read_text(encoding="utf-8"))


def plan(decision: dict, claims: list[dict], decisions_file: Path | None = None) -> dict:
    base = {b["id"]: b for b in decision["baseline"]}
    claim = {c["id"]: c for c in claims}
    ref = load_decisions(decisions_file)
    pd = {d["id"]: d for d in ref["decisions"]}
    delegation = claim.get("N-BRIEF-planner_schedule_choices")
    decision_records = [{
        "id": d["id"], "summary": d["summary"], "value": d["value"], "kind": "planner-decision",
        "owner": ref["owner"], "status": ref["status"],
        "evidence_ids": ["N-BRIEF-planner_schedule_choices", "N-BRIEF-roster_change_owner"],
        "rationale": "The sources do not supply this value; the brief leaves it to the planner."}
        for d in ref["decisions"]]

    missing = [b for b in REQUIRED_BASELINE if base.get(b, {}).get("support") != "supported"]
    if delegation is None or delegation.get("support") != "supported":
        missing.append("N-BRIEF-planner_schedule_choices")
    if missing:
        return _unresolved(f"inputs not supported: {missing}", missing, decision_records)

    win, key, prog = base["B-event-window"]["value"], base["B-keynote"]["value"], base["B-programme"]["value"]
    ready, tear = base["B-readiness"]["value"], base["B-teardown"]["value"]
    start, end = datetime.fromisoformat(win["start"]), datetime.fromisoformat(win["end"])
    k_start, k_end = datetime.fromisoformat(key["start"]), datetime.fromisoformat(key["end"])
    if key["date"] != win["date"] or ready["date"] != win["date"] or not (start <= k_start < k_end <= end):
        return _unresolved("the keynote or readiness record is not on the event date inside the window",
                           ["B-keynote", "B-readiness", "B-event-window"], decision_records)

    def at(hhmm):
        h, m = map(int, hhmm.split(":"))
        return start.replace(hour=h, minute=m)

    blocks: list[dict] = []

    def add(kind, label, s, e, basis, evidence, decisions=()):
        blocks.append({"id": f"PRG-{len(blocks) + 1:02d}-{kind}", "kind": kind, "label": label,
                       "start": s.isoformat(), "end": e.isoformat(), "minutes": int((e - s).total_seconds() // 60),
                       "basis": basis, "evidence_ids": list(evidence), "decision_ids": list(decisions),
                       "owner": "Programme"})

    add("setup", "Setup and pre-opening readiness checks", at(ready["setup"]["start"]), at(ready["setup"]["end"]),
        SOURCE, ["B-readiness", "B-venue-hold"])

    roster = prog["roster"]
    first = math.ceil(len(roster) / 2)
    groups = {"demos-1": roster[:first], "demos-2": roster[first:]}
    minutes = {"opening": pd["PD-opening-minutes"]["value"], "lunch": pd["PD-lunch-minutes"]["value"],
               "break": pd["PD-break-minutes"]["value"], "closing": pd["PD-closing-minutes"]["value"]}
    order = pd["PD-order"]["value"]
    if order.count("break") != pd["PD-break-count"]["value"] or order[-1] != "closing" or "keynote" not in order:
        return _unresolved("PD-order is inconsistent with the break count or does not end with closing",
                           ["PD-order", "PD-break-count"], decision_records)
    t = start
    breaks = 0
    for step in order:
        if step == "keynote":
            if t > k_start:
                return _unresolved("items before the keynote do not fit before its fixed start",
                                   ["B-keynote", "PD-opening-minutes"], decision_records)
            if t < k_start:
                add("buffer", "Unallocated Programme buffer", t, k_start, UNALLOCATED, ["B-event-window"], ["PD-order"])
            add("keynote", "Keynote", k_start, k_end, SOURCE, ["B-keynote", "B-programme"])
            t = k_end
        elif step == "closing":
            c_start = end - timedelta(minutes=minutes["closing"])
            if t > c_start:
                return _unresolved("the programme does not fit inside the event window",
                                   ["B-event-window", "PD-order"], decision_records)
            if t < c_start:
                add("buffer", "Unallocated Programme buffer", t, c_start, UNALLOCATED, ["B-event-window"], ["PD-order"])
            add("closing", "Closing", c_start, end, PLANNER, ["B-event-window"], ["PD-closing-minutes", "PD-order"])
            t = end
        elif step in groups:
            for demo in groups[step]:
                s = t
                t = s + timedelta(minutes=prog["presentation_minutes"])
                add("demo", f"{demo} presentation", s, t, MIXED, ["B-programme"], ["PD-order", "PD-demo-grouping"])
                s = t
                t = s + timedelta(minutes=prog["changeover_minutes"])
                add("changeover", f"{demo} changeover", s, t, MIXED, ["B-programme"], ["PD-order", "PD-demo-grouping"])
        elif step == "break":
            breaks += 1
            s, t = t, t + timedelta(minutes=minutes["break"])
            add("break", f"Break {breaks}", s, t, PLANNER, ["N-BRIEF-planner_schedule_choices"],
                ["PD-break-minutes", "PD-break-count", "PD-order"])
        elif step in ("opening", "lunch"):
            s, t = t, t + timedelta(minutes=minutes[step])
            add(step, step.capitalize() if step == "lunch" else "Opening and welcome", s, t, PLANNER,
                ["B-event-window" if step == "opening" else "N-BRIEF-planner_schedule_choices"],
                [f"PD-{step}-minutes", "PD-order"])
        else:
            return _unresolved(f"unknown step '{step}' in PD-order", ["PD-order"], decision_records)

    add("teardown", "Teardown; all vendors clear", datetime.fromisoformat(tear["start"]),
        datetime.fromisoformat(tear["end"]), SOURCE, ["B-teardown", "B-readiness"])
    problems = check(blocks, start, end)
    if problems:
        return _unresolved("; ".join(problems), ["PD-order"], decision_records)
    unallocated = sum(b["minutes"] for b in blocks if b["kind"] == "buffer")
    return {"status": "planned", "reason": None, "date": win["date"], "blocks": blocks,
            "decisions": decision_records, "unallocated_minutes": unallocated,
            "evidence_ids": list(REQUIRED_BASELINE) + ["N-BRIEF-planner_schedule_choices"],
            "demo_count": len(roster), "missing_inputs": []}


def check(blocks: list[dict], window_start: datetime, window_end: datetime) -> list[str]:
    """No overlaps; programme items inside the event window; setup before it and teardown after it."""
    problems = []
    ordered = sorted(blocks, key=lambda b: b["start"])
    for a, b in zip(ordered, ordered[1:]):
        if datetime.fromisoformat(a["end"]) > datetime.fromisoformat(b["start"]):
            problems.append(f"{a['id']} overlaps {b['id']}")
    for b in blocks:
        s, e = datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])
        if e <= s:
            problems.append(f"{b['id']} has no duration")
        if b["kind"] == "setup" and e > window_start:
            problems.append(f"{b['id']} runs into the event window")
        elif b["kind"] == "teardown" and s < window_end:
            problems.append(f"{b['id']} starts before the event window closes")
        elif b["kind"] not in ("setup", "teardown") and (s < window_start or e > window_end):
            problems.append(f"{b['id']} is outside the event window")
    return problems


def _unresolved(reason, missing, decisions) -> dict:
    return {"status": "unresolved", "reason": reason, "date": None, "blocks": [], "decisions": decisions,
            "unallocated_minutes": None, "evidence_ids": [m for m in missing if not m.startswith("PD-")] or ["ASG-PROGRAMME"],
            "demo_count": None, "missing_inputs": missing}
