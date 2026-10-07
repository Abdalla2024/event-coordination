import json

import pytest

from coordination.snapshots import STAGES, ChainError, SnapshotChain, load_validator, new_run_id, verify_chain

EXTERNAL = {"STK-I1-L73", "ASG-CLOCK"}
H = "sha256:" + "0" * 64


def rec(i, ev=("STK-I1-L73",)):
    return {"id": i, "summary": f"record {i}", "evidence_ids": list(ev)}


def source(i):
    return {**rec(i), "source_role": "budget", "locator": "https://x.test", "retrieved_at": "2026-10-07T00:00:00Z",
            "retrieval_status": "retrieved", "content_type": "text/csv", "version_metadata": None,
            "content_hash": H, "local_reference": None,
            "observations": [{"id": f"OBS-{i}", "summary": "o", "locator": {"kind": "cell-range", "value": "A1"}}]}


def decision(i, ev):
    return {**rec(i, ev), "rationale": "because", "tradeoffs": ["t"]}


# (state, consumed, produced) for each stage, chained through record ids
PLAN = {
    "scope-and-approval-gates": ({"objective": "o", "decision_deadline": "2026-09-04T17:00:00+08:00",
                                  "owners": ["Operations"], "approval_gates": ["plan"], "gate": rec("GATE-1")},
                                 [], ["GATE-1"]),
    "source-capture": ({"sources": [source("SRC-A")]}, ["GATE-1"], ["SRC-A"]),
    "constraint-model": ({"hard_constraints": [rec("HC-1", ["OBS-SRC-A"])], "preferences": [], "assumptions": [],
                          "unknowns": [], "conflicts": []}, ["SRC-A"], ["HC-1"]),
    "planning-baseline": ({"headcount_basis": [rec("HB-1", ["HC-1"])], "schedule_dependencies": [],
                           "budget_baseline": [], "accessibility_baseline": []}, ["HC-1"], ["HB-1"]),
    "option-generation": ({"options": [rec("OPT-1", ["HB-1"])], "rejected_early": []}, ["HB-1"], ["OPT-1"]),
    "feasibility-testing": ({"option_results": [{**rec("FR-1", ["OPT-1"]), "feasibility": "conditional"}],
                             "unresolved_conditions": []}, ["OPT-1"], ["FR-1"]),
    "decision-and-approval": ({"recommendation": None, "tradeoffs": [], "learner_decisions": [],
                               "approval_requirements": [{**rec("APR-1", ["FR-1"]), "status": "pending"}]},
                              ["FR-1"], ["APR-1"]),
    "draft-propagation": ({"artifact_drafts": [{"id": "ART-1", "path": "event-plan.md", "sha256": H,
                                                "validation_status": "valid"}],
                           "affected_dependencies": [], "unresolved_items": []}, ["APR-1"], ["ART-1"]),
    "publication-validation": ({"artifacts": [{"id": "PUB-1", "path": "event-plan.md", "sha256": H,
                                               "validation_status": "valid"}],
                                "validation_checks": [rec("VC-1", ["ART-1"])], "publication_status": "validated"},
                               ["ART-1"], ["PUB-1", "VC-1"]),
}


@pytest.fixture
def validator(config):
    return load_validator(config.schema_path)


@pytest.fixture
def chain(tmp_path, validator, config):
    return SnapshotChain(tmp_path, new_run_id(), validator, config.schema_version, EXTERNAL)


def write_all(chain, upto=len(STAGES)):
    for stage in STAGES[:upto]:
        state, consumed, produced = PLAN[stage]
        chain.write(stage, "partial", state, consumed, produced)


def test_full_chain_is_valid_and_linked(tmp_path, chain, validator):
    write_all(chain)
    assert verify_chain(tmp_path, validator, EXTERNAL) == []
    docs = [json.loads((tmp_path / e["path"]).read_text()) for e in chain.written]
    assert docs[0]["predecessor"] is None
    assert len({d["run_id"] for d in docs}) == 1 and len({d["snapshot_id"] for d in docs}) == 9
    for prev, d in zip(chain.written, docs[1:]):
        assert d["predecessor"] == {"snapshot_id": prev["snapshot_id"], "path": prev["path"], "sha256": prev["sha256"]}
    assert [p.name for p in sorted((tmp_path / "snapshots").glob("*.json"))][0] == "01-scope-and-approval-gates.json"


def test_tampering_is_detected(tmp_path, chain, validator):
    write_all(chain)
    p = tmp_path / chain.written[3]["path"]
    doc = json.loads(p.read_text())
    doc["status"] = "complete"
    p.write_text(json.dumps(doc))
    problems = verify_chain(tmp_path, validator, EXTERNAL)
    assert any("05-option-generation.json: predecessor" in x for x in problems)


def test_missing_snapshot_detected(tmp_path, chain, validator):
    write_all(chain)
    (tmp_path / chain.written[8]["path"]).unlink()
    assert any("missing" in x for x in verify_chain(tmp_path, validator, EXTERNAL))


def test_out_of_order_rejected(chain):
    state, consumed, produced = PLAN["source-capture"]
    with pytest.raises(ChainError, match="expected stage"):
        chain.write("source-capture", "partial", state, consumed, produced)


def test_consumed_must_be_produced_earlier(chain):
    write_all(chain, 1)
    state, _, produced = PLAN["source-capture"]
    with pytest.raises(ChainError, match="consumed ids not produced"):
        chain.write("source-capture", "partial", state, ["NOPE"], produced)


def test_dangling_evidence_rejected(chain):
    state, consumed, produced = PLAN["scope-and-approval-gates"]
    bad = {**state, "gate": rec("GATE-1", ["UNKNOWN-EVIDENCE"])}
    with pytest.raises(ChainError, match="do not resolve"):
        chain.write("scope-and-approval-gates", "partial", bad, consumed, produced)


def test_produced_must_be_defined(chain):
    state, consumed, _ = PLAN["scope-and-approval-gates"]
    with pytest.raises(ChainError, match="not defined"):
        chain.write("scope-and-approval-gates", "partial", state, consumed, ["GHOST"])


def test_schema_violation_rejected_and_nothing_written(tmp_path, chain):
    state, consumed, produced = PLAN["scope-and-approval-gates"]
    with pytest.raises(ChainError, match="decision_deadline"):
        chain.write("scope-and-approval-gates", "partial", {**state, "decision_deadline": "soon"}, consumed, produced)
    assert not (tmp_path / "snapshots").exists()


def test_captured_source_records_form_a_valid_stage_02(tmp_path, validator, config, sources, fixture_bytes):
    from conftest import FakeTransport, ok
    from coordination.config import load_requirements_evidence
    from coordination.sources import capture_all

    hall = sources["SRC-TICC-HALL"]
    t = FakeTransport({hall["retrieval"]["request_url"]: [ok(fixture_bytes("rejected.html"), "text/html"),
                                                           ok(fixture_bytes("ticc-hall.html"), "text/html")]})
    results = capture_all([hall, sources["SRC-TICC-4F"]], config.http_profiles, t, tmp_path)
    records = [r.record for r in results.values()]
    ch = SnapshotChain(tmp_path, new_run_id(), validator, config.schema_version, load_requirements_evidence())
    state, consumed, produced = PLAN["scope-and-approval-gates"]
    ch.write("scope-and-approval-gates", "partial", state, consumed, produced)
    ch.write("source-capture", "partial", {"sources": records}, ["GATE-1"], [r["id"] for r in records])
    doc = json.loads((tmp_path / ch.written[1]["path"]).read_text())
    hall_rec = doc["state"]["sources"][0]
    assert [a["outcome"] for a in hall_rec["attempts"]] == ["rejected", "retrieved"]
    assert doc["state"]["sources"][1]["retrieval_status"] == "unavailable"


def test_extra_fields_cannot_override(chain):
    state, consumed, produced = PLAN["scope-and-approval-gates"]
    with pytest.raises(ChainError, match="override"):
        chain.write("scope-and-approval-gates", "partial", state, consumed, produced, extra={"run_id": "x"})
    chain.write("scope-and-approval-gates", "partial", state, consumed, produced,
                extra={"supersedes_run_id": None})
