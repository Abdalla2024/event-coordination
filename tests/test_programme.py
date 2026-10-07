"""Phase 5 run-of-show planning."""

import copy
import json

from factories import decided, render_input, twelve_demo_brief
from coordination.programme import load_decisions, plan


def _decisions_file(tmp_path, **values):
    ref = load_decisions()
    for d in ref["decisions"]:
        if d["id"] in values:
            d["value"] = values[d["id"]]
    f = tmp_path / "pd.json"
    f.write_text(json.dumps(ref))
    return f


def schedule(prog):
    return [(b["kind"], b["start"][11:16], b["end"][11:16]) for b in prog["blocks"]]


def test_twelve_demo_schedule_matches_the_approved_plan(tmp_path):
    prog = render_input(tmp_path, SRC_BRIEF=twelve_demo_brief()).programme
    assert prog["status"] == "planned"
    s = schedule(prog)
    assert s[:5] == [("setup", "07:30", "09:30"), ("opening", "09:30", "09:45"), ("buffer", "09:45", "10:00"),
                     ("keynote", "10:00", "11:00"), ("break", "11:00", "11:15")]
    assert ("demo", "11:15", "11:25") in s and ("changeover", "12:30", "12:33") in s
    assert ("lunch", "12:33", "13:33") in s and ("demo", "14:38", "14:48") in s
    assert s[-4:] == [("break", "14:51", "15:06"), ("buffer", "15:06", "16:45"), ("closing", "16:45", "17:00"),
                      ("teardown", "17:00", "18:30")]
    assert prog["unallocated_minutes"] == 114
    demos = [b for b in prog["blocks"] if b["kind"] == "demo"]
    assert [b["label"].split()[0] for b in demos] == [f"DEMO-{i:02d}" for i in range(1, 13)]
    assert len([b for b in prog["blocks"] if b["kind"] == "changeover"]) == 12


def test_no_overlaps_and_bases_labelled(tmp_path):
    prog = render_input(tmp_path, SRC_BRIEF=twelve_demo_brief()).programme
    blocks = sorted(prog["blocks"], key=lambda b: b["start"])
    for a, b in zip(blocks, blocks[1:]):
        assert a["end"] <= b["start"]
    basis = {b["kind"]: b["basis"] for b in prog["blocks"]}
    assert basis["keynote"] == basis["setup"] == basis["teardown"] == "source"
    assert basis["opening"] == basis["lunch"] == basis["break"] == basis["closing"] == "planner-decision"
    assert basis["demo"] == "source-duration, planner-placement" and basis["buffer"] == "unallocated"
    pd_ids = {d["id"] for d in prog["decisions"]}
    for b in prog["blocks"]:
        if b["basis"] != "source":
            assert b["decision_ids"] and set(b["decision_ids"]) <= pd_ids
    assert all(d["owner"] == "Programme" and "pending Programme review" in d["status"] for d in prog["decisions"])


def test_planner_values_come_from_the_decisions_file(tmp_path):
    prog = render_input(tmp_path, SRC_BRIEF=twelve_demo_brief(),
                        decisions_file=_decisions_file(tmp_path, **{"PD-lunch-minutes": 45})).programme
    lunch = next(b for b in prog["blocks"] if b["kind"] == "lunch")
    assert lunch["minutes"] == 45 and prog["unallocated_minutes"] == 129


def test_programme_that_does_not_fit_is_unresolved(tmp_path):
    prog = render_input(tmp_path, SRC_BRIEF=twelve_demo_brief(),
                        decisions_file=_decisions_file(tmp_path, **{"PD-lunch-minutes": 400})).programme
    assert prog["status"] == "unresolved" and prog["blocks"] == [] and "does not fit" in prog["reason"]


def test_opening_overrunning_the_keynote_is_unresolved(tmp_path):
    prog = render_input(tmp_path, decisions_file=_decisions_file(tmp_path, **{"PD-opening-minutes": 45})).programme
    assert prog["status"] == "unresolved" and "keynote" in prog["reason"]


def test_inconsistent_order_is_unresolved(tmp_path):
    prog = render_input(tmp_path, decisions_file=_decisions_file(
        tmp_path, **{"PD-order": ["opening", "keynote", "break", "demos-1", "lunch", "demos-2", "closing"]})).programme
    assert prog["status"] == "unresolved"


def test_missing_planner_delegation_is_unresolved(tmp_path):
    from factories import BRIEF, brief_blocks
    i = next(i for i, (_, x) in enumerate(BRIEF) if "The planner chooses" in x)
    prog = render_input(tmp_path, SRC_BRIEF=brief_blocks({i: BRIEF[i][1].replace(
        "The planner chooses the demonstration order, grouping and compatible meal and break schedule. ", "")})).programme
    assert prog["status"] == "unresolved" and "N-BRIEF-planner_schedule_choices" in prog["missing_inputs"]


def test_missing_calendar_is_unresolved(tmp_path):
    prog = render_input(tmp_path, SRC_CALENDAR=None).programme
    assert prog["status"] == "unresolved" and prog["blocks"] == []


def test_plan_does_not_modify_the_decision_model(tmp_path):
    m, n = decided(tmp_path)
    d, c = m.as_dict(), n.as_records()
    before = copy.deepcopy((d, c))
    plan(d, c)
    assert (d, c) == before
