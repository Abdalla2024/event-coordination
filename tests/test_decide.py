"""Phase 3 decision and feasibility layer."""

from factories import ATT, ATT_H, BRIEF, CAL, CAL_H, VEN, VEN_H, decided, notion
from conftest import xlsx_bytes
from coordination.config import load_requirements_evidence

A, B = "OPT-2026-10-17-Q-003", "OPT-2026-10-17-Q-004"
A7, B7 = f"{A}-sub-Q-007", f"{B}-sub-Q-007"
A8, B8 = f"{A}-add-Q-008", f"{B}-add-Q-008"
FALL = "OPT-2026-10-24-fallback"


def ven(rows):
    return xlsx_bytes([VEN_H] + rows, "Vendor Quotes")


def check(model, cid):
    return next(c for c in model.checks if c["id"] == cid)


def status(model):
    return {o["id"]: o["feasibility"] for o in model.options}


# ---------- classifications ----------

def test_option_set_and_classifications(tmp_path):
    m, _ = decided(tmp_path)
    assert status(m) == {A: "conditional", B: "conditional", A7: "infeasible", B7: "infeasible",
                         A8: "infeasible", B8: "infeasible", FALL: "infeasible"}
    assert m.option(A)["quote_ids"] == ["Q-001", "Q-003", "Q-005", "Q-006", "Q-009", "Q-010"]
    assert m.option(A8)["quote_ids"][-1] == "Q-008" and m.option(A7)["quote_ids"][3] == "Q-007"


def test_no_option_is_feasible_and_shortfall_is_recorded(tmp_path):
    m, _ = decided(tmp_path)
    assert not [o for o in m.options if o["feasibility"] == "feasible"]
    u = next(u for u in m.unresolved if u["id"] == "UNR-feasible-option-shortfall")
    assert u["owner"] == "Operations" and u["feasible_options"] == []


def test_genuinely_supported_hard_checks_pass(tmp_path):
    m, _ = decided(tmp_path)
    for name in ("date", "keynote", "venue-window", "readiness", "capacity-venue", "capacity-catering-Q-003",
                 "capacity-quiet-room", "capacity-wheelchair", "capacity-live_captions", "capacity-hearing_loop",
                 "capacity-security", "access-hearing_loop", "access-live_captions", "access-staffed_quiet_room",
                 "access-wheelchair_seating", "access-step_free_access", "dietary", "budget-ceiling",
                 "Q-003-validity", "budget-catering"):
        assert check(m, f"CHK-{A}-{name}")["outcome"] == "pass", name


def test_feasible_only_when_every_condition_is_evidenced(tmp_path):
    def evidence_everything(n):
        for c in n.of_kind("prerequisite"):
            c.fields["completion_evidence"] = ["EVID-TEST"]
        for c in n.of_kind("vendor-quote"):
            c.fields["confirmation_evidence"] = ["EVID-TEST"]
    m, _ = decided(tmp_path, mutate=evidence_everything)
    assert status(m)[A] == "feasible" and status(m)[B] == "feasible"
    assert status(m)[A7] == "infeasible"          # evidence of confirmation never cures a hard failure


def test_one_open_condition_keeps_option_conditional(tmp_path):
    def all_but_briefing(n):
        for c in n.of_kind("prerequisite"):
            if c.id != "P-ticc-technical-safety-briefing":
                c.fields["completion_evidence"] = ["EVID-TEST"]
        for c in n.of_kind("vendor-quote"):
            c.fields["confirmation_evidence"] = ["EVID-TEST"]
    m, _ = decided(tmp_path, mutate=all_but_briefing)
    assert status(m)[A] == "conditional"
    assert [s for s in m.option(A)["blocking"]["open"]] == [
        "TICC technical coordination meeting and safety evacuation briefing: required condition with no evidence "
        "of completion."]


# ---------- named failures ----------

def test_q007_hearing_loop_gap(tmp_path):
    m, _ = decided(tmp_path)
    c = check(m, f"CHK-{A7}-access-hearing_loop")
    assert c["outcome"] == "fail" and "N-QUOTE-Q-007" in c["evidence_ids"] and "STK-I2-L77" in c["evidence_ids"]


def test_q008_ceiling_failure_and_open_prerequisites(tmp_path):
    m, _ = decided(tmp_path)
    assert check(m, f"CHK-{A8}-budget-ceiling")["outcome"] == "fail"
    for name in ("P-livestream-network-test-Q-008", "P-livestream-venue-confirmation-Q-008", "readiness",
                 "Q-008-confirmation"):
        assert check(m, f"CHK-{A8}-{name}")["outcome"] == "open", name
    prod = check(m, f"CHK-{A8}-budget-production")
    assert prod["outcome"] == "open" and "explicit approval by Programme" in prod["summary"]


def test_24_october_keynote_conflict(tmp_path):
    m, _ = decided(tmp_path)
    k = check(m, f"CHK-{FALL}-keynote")
    assert k["outcome"] == "fail" and {"N-CAL-CAL-004", "N-QUOTE-Q-002"} <= set(k["evidence_ids"])
    o = m.option(FALL)
    assert o["service_gaps"] == ["accessibility", "catering", "production", "security"]
    assert o["costs"]["total_with_allowances_twd"] is None and "no quotes" in o["costs"]["incomplete_reason"]


def test_unconfirmed_venue_is_open_not_confirmed(tmp_path):
    m, _ = decided(tmp_path)
    v = check(m, f"CHK-{A}-P-venue-confirmation")
    assert v["outcome"] == "open" and v["owner"] == "Operations"
    assert not any(c["id"] == f"CHK-{A}-Q-001-confirmation" for c in m.checks)


def test_accessibility_gap_fails(tmp_path):
    rows = [r if r[0] != "Q-005" else r[:3] + ["transcript service"] + r[4:] for r in VEN]
    m, _ = decided(tmp_path, SRC_VENDOR=ven(rows))
    assert check(m, f"CHK-{A}-access-live_captions")["outcome"] == "fail"
    assert status(m)[A] == "infeasible"


def test_catering_shortage_fails(tmp_path):
    rows = [r if r[0] != "Q-003" else r[:5] + [200] + r[6:] for r in VEN]
    m, _ = decided(tmp_path, SRC_VENDOR=ven(rows))
    assert check(m, f"CHK-{A}-capacity-catering-Q-003")["outcome"] == "fail" and status(m)[A] == "infeasible"
    assert status(m)[B] == "conditional"


# ---------- budget ----------

def test_approval_limit_variances(tmp_path):
    m, _ = decided(tmp_path)
    cat = check(m, f"CHK-{B}-budget-catering")
    assert cat["outcome"] == "pass" and "+11000" in cat["summary"] and "ordinary approval by Operations" in cat["summary"]
    sec = check(m, f"CHK-{A}-budget-security")
    assert sec["outcome"] == "pass" and "+3000" in sec["summary"]
    apr = {a["id"]: a for a in m.approvals}
    assert apr[f"APR-{B}-budget-catering"]["explicit_required"] is False
    assert apr[f"APR-{A8}-budget-production"]["explicit_required"] is True
    assert all(a["status"] == "pending" for a in m.approvals)
    assert apr[f"APR-{A}-budget-communications"]["allowance"] is True


def test_ceiling_failure_from_price_change(tmp_path):
    rows = [r if r[0] != "Q-004" else r[:4] + [140000] + r[5:] for r in VEN]
    m, _ = decided(tmp_path, SRC_VENDOR=ven(rows))
    b = m.option(B)
    assert b["costs"]["total_with_allowances_twd"] == 526000 and b["feasibility"] == "infeasible"
    assert check(m, f"CHK-{B}-budget-catering")["outcome"] == "open"     # 140000 > 135000 limit


def test_deterministic_costs(tmp_path):
    m1, _ = decided(tmp_path / "1")
    m2, _ = decided(tmp_path / "2")
    expect = {A: (429000, 494000, 26000), B: (447000, 512000, 8000), A7: (403000, 468000, 52000),
              A8: (484000, 549000, -29000), B8: (502000, 567000, -47000)}
    for oid, (vendor, total, rem) in expect.items():
        c = m1.option(oid)["costs"]
        assert (c["vendor_total_twd"], c["total_with_allowances_twd"], c["remaining_under_ceiling_twd"]) == (vendor, total, rem)
        assert c["allowances_twd"] == {"communications": 25000, "contingency": 40000}
    assert [o["costs"] for o in m1.options] == [o["costs"] for o in m2.options]


def test_commitments_are_not_combined_by_invented_formula(tmp_path):
    from factories import BUD, BUD_H
    rows = [r if r[0] != "venue" else r[:3] + [10000] + r[4:] for r in BUD]
    m, _ = decided(tmp_path, SRC_BUDGET=xlsx_bytes([BUD_H] + rows, "Budget"))
    c = check(m, f"CHK-{A}-budget-commitments")
    assert c["outcome"] == "unverified" and status(m)[A] == "unverified"
    assert m.option(A)["costs"]["total_with_allowances_twd"] == 494000   # commitment reported, not added


def test_case_venue_amount_kept_and_tariff_noted(tmp_path):
    m, _ = decided(tmp_path)
    assert m.option(A)["costs"]["categories"]["venue"]["amount_twd"] == 155000
    note = next(n for n in m.notes if n["id"] == "NOTE-venue-tariff")
    assert note["planning_value_replaced"] is False and "170000" in note["summary"]


# ---------- stale, conflicting, missing ----------

def test_expired_quote_makes_option_unverified(tmp_path):
    rows = [r if r[0] != "Q-003" else r[:7] + ["2026-08-25"] + r[8:] for r in VEN]
    m, _ = decided(tmp_path, SRC_VENDOR=ven(rows))
    assert check(m, f"CHK-{A}-Q-003-validity")["outcome"] == "unverified"
    assert status(m)[A] == "unverified" and status(m)[B] == "conditional"


def test_conflicting_headcount_blocks_capacity(tmp_path):
    rows = ATT + [["SIG-099", "late_form", "fellows", "registered_attendees", 150, "people", "2026-08-25", "high"]]
    m, _ = decided(tmp_path, SRC_ATTENDEE=xlsx_bytes([ATT_H] + rows, "Attendee Signals"))
    assert m.baseline.elements["B-headcount"].support == "unresolved"
    c = check(m, f"CHK-{A}-capacity-catering-Q-003")
    assert c["outcome"] == "unverified" and "N-ATT-group-fellows" in str(m.baseline.elements["B-headcount"].blocked_by)
    assert status(m)[A] == "unverified"
    assert any(u["id"] == "UNR-B-headcount" for u in m.unresolved)


def test_conflicting_ceiling_blocks_budget_decision(tmp_path):
    text = BRIEF[8][1].replace("TWD 520,000 ceiling", "TWD 480,000 ceiling")
    blocks = [(t, text if i == 8 else x) for i, (t, x) in enumerate(BRIEF)]
    m, _ = decided(tmp_path, SRC_BRIEF=notion(blocks))
    assert check(m, f"CHK-{A}-budget-ceiling")["outcome"] == "unverified"
    assert m.option(A)["costs"]["remaining_under_ceiling_twd"] is None
    assert status(m)[A] == "unverified"


def test_quote_term_conflict_unverified(tmp_path):
    dup = ["Q-011", "Green Table", "catering", "lunch and two breaks", 99000, 260, "2026-10-17", "2026-09-07",
           "available", ""]
    m, _ = decided(tmp_path, SRC_VENDOR=ven(VEN + [dup]))
    assert check(m, f"CHK-{A}-Q-003-terms")["outcome"] == "unverified"


def test_floor_plan_unavailable_withholds_spatial_accessibility(tmp_path):
    m, _ = decided(tmp_path, SRC_TICC_4F=None)
    assert check(m, f"CHK-{A}-access-step_free_access")["outcome"] == "unverified"
    assert check(m, f"CHK-{A}-access-wheelchair_seating")["outcome"] == "unverified"
    assert status(m)[A] == "unverified"


def test_missing_calendar_prevents_option_generation(tmp_path):
    m, _ = decided(tmp_path, SRC_CALENDAR=None)
    assert m.options == [] and any(u["id"] == "GEN-base" for u in m.unresolved)


def test_missing_keynote_row_is_unverified_not_passed(tmp_path):
    rows = [r for r in CAL if r[0] != "CAL-004"]
    m, _ = decided(tmp_path, SRC_CALENDAR=xlsx_bytes([CAL_H] + rows, "Calendar Constraints"))
    assert check(m, f"CHK-{A}-keynote")["outcome"] == "unverified"


# ---------- traceability ----------

def test_every_check_and_record_is_evidence_linked(tmp_path):
    m, n = decided(tmp_path)
    known = set(load_requirements_evidence()) | {c.id for c in n.claims} | set(m.baseline.elements)
    known |= {c["id"] for c in m.checks}
    for rec in m.checks + m.options + m.approvals + m.dependencies + m.unresolved + m.comparison + m.notes:
        assert rec["evidence_ids"], rec["id"]
        assert set(rec["evidence_ids"]) <= known, (rec["id"], set(rec["evidence_ids"]) - known)
    for c in m.checks:
        if c["outcome"] != "pass":
            assert c["rationale"], c["id"]


def test_dependencies_have_owners_and_no_deadlines(tmp_path):
    m, _ = decided(tmp_path)
    deps = {d["id"]: d for d in m.dependencies}
    assert deps["DEP-P-ticc-technical-safety-briefing"]["owner"] == "Operations"
    assert deps["DEP-P-accessibility-walkthrough"]["owner"] == "Learner Experience"
    assert all(d["deadline"] is None for d in m.dependencies)


def test_vendor_experience_not_scored_and_no_recommendation(tmp_path):
    m, _ = decided(tmp_path)
    assert next(n for n in m.notes if n["id"] == "NOTE-vendor-experience")["support"] == "unresolved"
    assert all(c["vendor_experience"] == "not evidenced; not scored" for c in m.comparison)
    d = m.as_dict()
    assert d["recommendation"] is None
    assert {c["option_id"] for c in m.comparison} == {A, B}
    a = next(c for c in m.comparison if c["option_id"] == A)
    assert a["catering_buffer_people"] == 15
    assert a["category_variances_twd"] == {"catering": -7000, "accessibility": -5000, "production": -7000,
                                           "security": 3000}
