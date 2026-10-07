"""Phase 4 recommendation layer."""

import copy
import json

from factories import ATT, ATT_H, CAL, CAL_H, VEN, VEN_H, decided
from conftest import xlsx_bytes
from coordination.config import load_config, load_requirements_evidence
from coordination.recommend import condition_types, recommend, run_status
from coordination.snapshots import load_validator, schema_errors

A, B = "OPT-2026-10-17-Q-003", "OPT-2026-10-17-Q-004"


def ven(rows):
    return xlsx_bytes([VEN_H] + rows, "Vendor Quotes")


def q(qid, **changes):
    """VEN rows with one quote's amount/capacity/valid_until replaced."""
    idx = {"amount": 4, "capacity": 5, "valid_until": 7}
    rows = []
    for r in VEN:
        r = list(r)
        if r[0] == qid:
            for k, v in changes.items():
                r[idx[k]] = v
        rows.append(r)
    return ven(rows)


def run(tmp_path, **kw):
    m, n = decided(tmp_path, **kw)
    return m, n, recommend(m, n)


def evidence_everything(n):
    for c in n.of_kind("prerequisite"):
        c.fields["completion_evidence"] = ["EVID-TEST"]
    for c in n.of_kind("vendor-quote"):
        c.fields["confirmation_evidence"] = ["EVID-TEST"]


def factor(rec, name):
    return next(f for f in rec.factors if f["factor"] == name)


# ---------- outcomes ----------

def test_live_like_case_defers_to_operations(tmp_path):
    m, _, rec = run(tmp_path)
    assert rec.status == "deferred-to-operations" and rec.recommendation is None
    assert rec.candidates == [A, B] and rec.operations_judgment_required
    cost, buf = factor(rec, "cost"), factor(rec, "catering_buffer")
    assert cost["values"] == {A: 494000, B: 512000} and cost["pairwise"][A][B] == "better"
    assert cost["details"][A]["remaining_under_ceiling_twd"] == 26000
    assert buf["values"] == {A: 15, B: 55} and buf["pairwise"][B][A] == "better"
    for f in ("open_conditions", "unverified_checks", "quote_validity"):
        assert factor(rec, f)["pairwise"][A][B] == "tie", f
    assert rec.question_for_operations == ("Operations judgment required: choose between lower cost and greater "
                                           f"budget headroom ({A}) and the larger catering capacity buffer ({B}).")
    assert {o["feasibility"] for o in m.options if o["id"] in (A, B)} == {"conditional"}
    assert {t["id"] for t in rec.tradeoffs} == {"TO-cost", "TO-catering_buffer"}
    assert rec.decision["recommendation"] is None and rec.decision["approval_status"] == "pending"


def test_clear_dominance_by_q003(tmp_path):
    _, _, rec = run(tmp_path, SRC_VENDOR=q("Q-004", capacity=260))      # same buffer, Q-004 still dearer
    assert rec.status == "recommended-conditional" and rec.recommendation == A
    assert "remains conditional on" in rec.decision["rationale"]
    assert not rec.operations_judgment_required


def test_clear_dominance_by_q004(tmp_path):
    _, _, rec = run(tmp_path, SRC_VENDOR=q("Q-004", amount=100000))     # cheaper and larger buffer
    assert rec.status == "recommended-conditional" and rec.recommendation == B


def test_infeasible_cheaper_option_is_excluded(tmp_path):
    m, _, rec = run(tmp_path)
    q007 = next(e for e in rec.excluded if e["option_id"] == f"{A}-sub-Q-007")
    assert m.option(q007["option_id"])["costs"]["total_with_allowances_twd"] < 494000
    assert q007["feasibility"] == "infeasible" and "Hearing loop" in q007["reason"]
    assert q007["option_id"] not in rec.candidates


def test_unverified_option_cannot_be_recommended_and_sole_candidate(tmp_path):
    _, _, rec = run(tmp_path, SRC_VENDOR=q("Q-003", valid_until="2026-08-25"))
    excluded = {e["option_id"]: e for e in rec.excluded}
    assert excluded[A]["feasibility"] == "unverified" and "expired" in excluded[A]["reason"]
    assert rec.candidates == [B]
    assert rec.status == "recommended-conditional" and rec.recommendation == B
    assert "only recommendable option" in rec.decision["rationale"]
    owners = {c["type"]: c["owners"] for c in rec.conditions[B]}
    assert owners["P-ticc-technical-safety-briefing"] == ["Operations"]
    assert owners["P-accessibility-walkthrough"] == ["Learner Experience"]
    assert all(c["type"] in rec.decision["rationale"] for c in rec.conditions[B])


def test_no_candidates_is_no_viable_option(tmp_path):
    rows = ATT + [["SIG-099", "late_form", "fellows", "registered_attendees", 150, "people", "2026-08-25", "high"]]
    m, _, rec = run(tmp_path, SRC_ATTENDEE=xlsx_bytes([ATT_H] + rows, "Attendee Signals"))
    assert rec.status == "no-viable-option" and rec.recommendation is None and rec.candidates == []
    assert any(u["id"] == "UNR-B-headcount" for u in rec.carried_unresolved)
    assert run_status([], m, rec)["status"] == "partial"


def test_missing_factor_value_prevents_dominance(tmp_path):
    # Without a decision deadline, quote validity through it is unknown: Q-003 would otherwise dominate.
    cal = xlsx_bytes([CAL_H] + [r for r in CAL if r[0] != "CAL-005"], "Calendar Constraints")
    _, _, rec = run(tmp_path, SRC_VENDOR=q("Q-004", capacity=260), SRC_CALENDAR=cal)
    assert factor(rec, "quote_validity")["pairwise"][A][B] == "not-comparable"
    assert rec.status == "deferred-to-operations" and rec.recommendation is None
    assert "not comparable" in rec.question_for_operations


def test_feasible_dominant_option_is_recommended(tmp_path):
    _, _, rec = run(tmp_path, SRC_VENDOR=q("Q-004", capacity=260), mutate=evidence_everything)
    assert rec.status == "recommended" and rec.recommendation == A


def test_fully_evidenced_options_can_still_defer(tmp_path):
    m, _, rec = run(tmp_path, mutate=evidence_everything)
    assert {o["feasibility"] for o in m.options if o["id"] in (A, B)} == {"feasible"}
    assert rec.status == "deferred-to-operations" and rec.recommendation is None


# ---------- condition types ----------

def test_condition_types_normalized_and_not_double_counted(tmp_path):
    m, _, rec = run(tmp_path)
    types_a = [c["type"] for c in rec.conditions[A]]
    types_b = [c["type"] for c in rec.conditions[B]]
    assert types_a == types_b                       # Q-003 vs Q-004 confirmations are the same type
    assert "confirmation:catering" in types_a and "P-venue-confirmation" in types_a
    quotes = {qid: c.value for qid, c in m.baseline.quotes.items()}
    a8 = condition_types(m.option(f"{A}-add-Q-008"), m.checks, quotes)
    assert "quote-condition:Q-008" not in a8         # folded into Q-008's named prerequisites
    assert len(a8["P-livestream-network-test-Q-008"]["check_ids"]) == 3   # prerequisite + status + readiness
    assert "explicit-approval:production" in a8


# ---------- invariants ----------

def test_phase3_model_is_not_modified(tmp_path):
    m, n = decided(tmp_path)
    before = copy.deepcopy(m.as_dict())
    recommend(m, n)
    assert m.as_dict() == before


def test_no_weights_or_scores(tmp_path):
    _, _, rec = run(tmp_path)
    text = json.dumps(rec.as_dict()).lower()
    for word in ('"weight', '"score', '"rank', "weighted"):
        assert word not in text, word


def test_deterministic(tmp_path):
    a = run(tmp_path / "a")[2].as_dict()
    b = run(tmp_path / "b")[2].as_dict()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_every_evidence_reference_resolves(tmp_path):
    m, n, rec = run(tmp_path)
    known = (set(load_requirements_evidence()) | {c.id for c in n.claims} | set(m.baseline.elements)
             | {c["id"] for c in m.checks} | {o["id"] for o in m.options} | {c["id"] for c in m.comparison}
             | {f["id"] for f in rec.factors})
    d = rec.as_dict()
    records = d["factors"] + d["excluded"] + d["stakeholder_context"] + [d["decision"]]
    for r in records:
        assert r["evidence_ids"] and set(r["evidence_ids"]) <= known, (r.get("id"), set(r["evidence_ids"]) - known)


def test_result_validates_as_stage_07(tmp_path):
    m, _, rec = run(tmp_path)
    cfg = load_config()
    doc = {"schema_version": cfg.schema_version, "snapshot_id": "c7", "run_id": "r", "stage": "decision-and-approval",
           "sequence": 7, "created_at": "2026-10-07T00:00:00Z", "status": "partial",
           "predecessor": {"snapshot_id": "p", "path": "snapshots/06.json", "sha256": "sha256:" + "0" * 64},
           "consumed_record_ids": [A], "produced_record_ids": ["DEC-recommendation"],
           "state": {"recommendation": rec.recommendation, "tradeoffs": rec.tradeoffs,
                     "learner_decisions": [rec.decision], "approval_requirements": m.approvals},
           "unresolved": rec.carried_unresolved, "decisions": [rec.decision]}
    assert schema_errors(load_validator(cfg.schema_path), doc) == []


# ---------- run status ----------

def test_run_status_semantics(tmp_path):
    m, n, rec = run(tmp_path)
    sources = [{"id": "S", "retrieval_status": "retrieved"}]
    s = run_status(sources, m, rec)
    assert s["status"] == "partial" and "requires Operations judgment" in s["reasons"][0]
    m2, n2, rec2 = run(tmp_path / "x", SRC_VENDOR=q("Q-004", capacity=260))
    assert run_status(sources, m2, rec2)["status"] == "complete"
    assert run_status([{"id": "S", "retrieval_status": "unavailable"}], m2, rec2)["status"] == "partial"
    m3, n3, rec3 = run(tmp_path / "y", SRC_CALENDAR=None)
    assert run_status(sources, m3, rec3)["status"] == "blocked"
    assert "failed" not in {run_status(sources, mm, rr)["status"] for mm, rr in ((m, rec), (m2, rec2), (m3, rec3))}
