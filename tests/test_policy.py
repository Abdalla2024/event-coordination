from datetime import datetime

import pytest

from coordination.policy import (Check, approval_record, category_check, ceiling_check, classify,
                                 prerequisite_check, quote_valid_at, tariff_difference_record,
                                 vendor_status_check)


def c(outcome, i="x"):
    return Check(i, "hard", outcome, "s")


def test_classification_precedence():
    assert classify([c("pass"), c("fail"), c("unverified"), c("open")])[0] == "infeasible"
    assert classify([c("pass"), c("unverified"), c("open")])[0] == "unverified"
    assert classify([c("pass"), c("open")])[0] == "conditional"
    assert classify([c("pass"), c("pass")])[0] == "feasible"
    assert classify([])[0] == "unverified"
    with pytest.raises(ValueError):
        Check("x", "hard", "maybe", "s")


def test_held_or_available_is_never_confirmation():
    for status in ("held", "available"):
        chk = vendor_status_check("V", "Q-001", status, [], ["OBS-1"], "Operations")
        assert chk.outcome == "open" and "STK-I3-L25" in chk.evidence_ids
    # every other check passing still leaves the option conditional
    hold = vendor_status_check("V", "Q-001", "held", [], [], "Operations")
    assert classify([c("pass"), c("pass"), hold])[0] == "conditional"
    assert vendor_status_check("V", "Q-008", "conditional", [], [], "Ops").outcome == "open"
    assert vendor_status_check("V", "Q-009", "booked", [], [], "Ops").outcome == "unverified"
    assert vendor_status_check("V", "Q-001", "held", ["EVID-CONFIRM"], [], "Ops").outcome == "pass"


def test_prerequisites_stay_open_without_evidence():
    p = prerequisite_check("P", "TICC technical and safety briefing", "Operations", [], ["STK-I3-L157"])
    assert p.outcome == "open" and p.owner == "Operations"
    assert "deadline" not in p.summary.lower()
    assert prerequisite_check("P", "walkthrough", "LX", ["EVID"], []).outcome == "pass"


def test_budget_rules():
    within = category_check("B", "catering", 126000, 115000, 135000, "Operations", [])
    assert within.outcome == "pass" and "+11000" in within.summary and "pending" in within.summary
    over = category_check("B", "production", 133000, 85000, 100000, "Programme", [])
    assert over.outcome == "open" and "STK-I3-L73" in over.evidence_ids
    assert ceiling_check("C", 512000, 520000, []).outcome == "pass"
    assert ceiling_check("C", 549000, 520000, []).outcome == "fail"


def test_quote_validity_at_business_clock():
    clock = datetime.fromisoformat("2026-08-26T12:00:00+08:00")
    assert quote_valid_at("2026-09-05", clock)
    assert quote_valid_at("2026-08-26", clock)
    assert not quote_valid_at("2026-08-25", clock)


def test_approvals_default_pending_and_need_complete_response():
    assert approval_record("A", "plan", "Operations", [])["status"] == "pending"
    partial = approval_record("A", "plan", "Operations", [], {"actor": "x", "outcome": "approved"})
    assert partial["status"] == "pending" and "missing" in partial["rationale"]
    deferred = approval_record("A", "plan", "Ops", [], {"actor": "x", "subject": "plan", "plan_revision": "r1",
                                                       "timestamp": "t", "outcome": "deferred", "reasons": "r"})
    assert deferred["status"] == "pending"


def test_tariff_difference_keeps_case_value():
    obs = {"id": "OBS-SRC-TICC-HALL-rate-weekend", "value": 170000}
    rec = tariff_difference_record("T", "Q-001", 155000, "2026-10-17", obs, ["OBS-SRC-VENDOR-Q-001"])
    assert rec["planning_value_twd"] == 155000 and rec["official_rate_twd_per_slot"] == 170000
    assert rec["event_day_kind"] == "weekend" and "not replaced" in rec["summary"]
    assert {"STK-I3-L205", "OBS-SRC-TICC-HALL-rate-weekend"} <= set(rec["evidence_ids"])
    missing = tariff_difference_record("T", "Q-001", 155000, "2026-10-17", None, [])
    assert missing["planning_value_twd"] == 155000 and missing["official_rate_twd_per_slot"] is None
