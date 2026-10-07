"""Phase 6: end-to-end run, nine-snapshot chain, history, supersede, recovery and failure.json."""

import json

import icalendar
import pytest

from conftest import FakeTransport, ok, xlsx_bytes
from factories import ATT, ATT_H, FIXED_TIME, VEN, VEN_H, bodies, decided, run_pipeline, twelve_demo_brief
from coordination import history, pipeline
from coordination.config import load_config, load_requirements_evidence, load_sources
from coordination.render.validate import affirmative_claims
from coordination.snapshots import STAGES, load_validator, snapshot_filename, verify_chain
from coordination.transport import HttpResponse

A, B = "OPT-2026-10-17-Q-003", "OPT-2026-10-17-Q-004"
V = load_validator(load_config().schema_path)
EXT = set(load_requirements_evidence())


def ven(rows):
    return xlsx_bytes([VEN_H] + rows, "Vendor Quotes")


def q004_capacity_260():
    return ven([r if r[0] != "Q-004" else r[:5] + [260] + r[6:] for r in VEN])


def snap(root, stage):
    return json.loads((root / "snapshots" / snapshot_filename(stage)).read_text())


def clean(root):
    return history.verify_current(root, V, EXT) + history.verify_history(root, V, EXT)


def text_files(root):
    """Every generated text artifact except raw captured evidence bytes."""
    return {p: p.read_text(encoding="utf-8") for p in root.rglob("*")
            if p.is_file() and "evidence" not in p.parts and p.suffix in (".json", ".md", ".csv", ".ics")}


# ---------- outcomes ----------

def test_partial_run_matches_the_live_result_shape(tmp_path):
    root = tmp_path / "d"
    r = run_pipeline(root)
    assert (r.status, r.exit_code) == ("partial", 10)
    ds = r.record["decision_summary"]
    assert ds["recommendation"] is None and ds["recommendation_status"] == "deferred-to-operations"
    assert [k for k, v in ds["options"].items() if v == "conditional"] == [A, B]
    assert "feasible" not in ds["options"].values()
    assert len(r.record["snapshots"]) == 9 and clean(root) == []
    s7, s9 = snap(root, "decision-and-approval"), snap(root, "publication-validation")
    assert s7["status"] == "partial" and s7["state"]["recommendation"] is None
    assert s9["status"] == "partial" and s9["state"]["publication_status"] == "validated"
    costs = {o["id"]: o["costs"]["total_with_allowances_twd"] for o in snap(root, "feasibility-testing")["state"]["option_results"]}
    assert costs[A] == 494000 and costs[B] == 512000
    assert all(a["status"] == "pending" for a in s7["state"]["approval_requirements"])


def test_complete_run(tmp_path):
    root = tmp_path / "d"
    r = run_pipeline(root, SRC_VENDOR=q004_capacity_260())
    assert (r.status, r.exit_code) == ("complete", 0)
    assert r.record["decision_summary"]["recommendation"] == A
    assert snap(root, "publication-validation")["status"] == "complete" and clean(root) == []


def test_blocked_run_keeps_nine_snapshots_and_empty_calendar(tmp_path):
    root = tmp_path / "d"
    r = run_pipeline(root, SRC_VENDOR=None)
    assert (r.status, r.exit_code) == ("blocked", 20)
    assert snap(root, "option-generation")["status"] == "blocked"
    assert snap(root, "publication-validation")["state"]["publication_status"] == "blocked"
    assert list(icalendar.Calendar.from_ical((root / "event-calendar.ics").read_text()).walk("VEVENT")) == []
    assert clean(root) == []


def test_unavailable_source_is_recorded_truthfully(tmp_path):
    root = tmp_path / "d"
    r = run_pipeline(root, SRC_TICC_HALL=None)
    assert r.status == "partial" and r.record["source_status"]["SRC-TICC-HALL"] == "unavailable"
    s2 = snap(root, "source-capture")
    hall = next(s for s in s2["state"]["sources"] if s["id"] == "SRC-TICC-HALL")
    assert s2["status"] == "partial" and hall["content_hash"] is None and hall["local_reference"] is None
    assert any("sources not retrieved" in x for x in r.record["status_reasons"])


def test_failed_source_retrieval_is_an_attempt_not_a_crash(tmp_path):
    srcs = load_sources()
    b = bodies(SRC_BRIEF=twelve_demo_brief())
    responses = {s["retrieval"]["request_url"]: [ok(b[s["id"]])] for s in srcs}
    hall = next(s for s in srcs if s["id"] == "SRC-TICC-HALL")["retrieval"]["request_url"]
    responses[hall] = [HttpResponse(500, {}, b"error", hall)]
    r = run_pipeline(tmp_path / "d", transport=FakeTransport(responses))
    s2 = snap(tmp_path / "d", "source-capture")
    hall_rec = next(s for s in s2["state"]["sources"] if s["id"] == "SRC-TICC-HALL")
    assert r.status == "partial" and hall_rec["retrieval_status"] == "unavailable"
    assert hall_rec["attempts"][0]["outcome"] == "http-error"


# ---------- snapshot chain ----------

def test_nine_snapshot_chain_is_linked_and_resolvable(tmp_path):
    root = tmp_path / "d"
    r = run_pipeline(root)
    docs = [snap(root, s) for s in STAGES]
    assert [d["sequence"] for d in docs] == list(range(1, 10))
    assert len({d["snapshot_id"] for d in docs}) == 9 and {d["run_id"] for d in docs} == {r.run_id}
    assert docs[0]["predecessor"] is None
    for prev, cur in zip(r.record["snapshots"], docs[1:]):
        assert cur["predecessor"] == {"snapshot_id": prev["snapshot_id"], "path": prev["path"], "sha256": prev["sha256"]}
    assert verify_chain(root, V, EXT) == []
    s1 = docs[0]["state"]
    assert s1["decision_deadline"] == "2026-09-04T17:00:00+08:00" and s1["supersedes_run_id"] is None
    assert any(p["kind"] == "page-region" for s in docs[1]["state"]["sources"] for p in
               [o["locator"] for o in s["observations"]])


def test_corrupted_snapshot_is_detected_and_preserved_on_recovery(tmp_path):
    root = tmp_path / "d"
    run_pipeline(root, run_id="run-1")
    run_pipeline(root, run_id="run-2")
    f = root / "snapshots" / snapshot_filename("option-generation")
    f.write_text(f.read_text().replace('"blocked"', '"x"').replace('"complete"', '"tampered"'))
    assert any("05-option-generation" in p for p in history.verify_current(root, V, EXT))
    r3 = run_pipeline(root, run_id="run-3")
    assert r3.status == "partial" and r3.record["recovery"]["attempted"]
    idx = {e["id"]: e for e in history.load_index(root)}
    assert idx["run-2"]["outcome"] == "invalid" and "05-option-generation" in idx["run-2"]["reason"]
    assert r3.record["supersedes_run_id"] == "run-1"          # latest valid state
    assert clean(root) == []


def test_broken_predecessor_reference_is_detected(tmp_path):
    root = tmp_path / "d"
    run_pipeline(root)
    f = root / "snapshots" / snapshot_filename("constraint-model")
    doc = json.loads(f.read_text())
    doc["predecessor"]["sha256"] = "sha256:" + "0" * 64
    f.write_text(json.dumps(doc))
    problems = verify_chain(root, V, EXT)
    assert any("03-constraint-model.json: predecessor" in p for p in problems)


# ---------- history and supersede ----------

def test_superseding_retains_the_prior_run(tmp_path):
    root = tmp_path / "d"
    run_pipeline(root, run_id="run-1")
    r2 = run_pipeline(root, run_id="run-2", SRC_VENDOR=q004_capacity_260())
    entry = history.load_index(root)[0]
    assert entry["run_id"] == "run-1" and entry["outcome"] == "superseded" and entry["superseded_by"] == "run-2"
    assert (root / "history" / "run-1" / "snapshots" / snapshot_filename("publication-validation")).exists()
    assert verify_chain(root / "history" / "run-1", V, EXT) == []
    s1 = snap(root, "scope-and-approval-gates")["state"]
    assert s1["supersedes_run_id"] == "run-1" and "SRC-VENDOR" in s1["changed_ids"]
    assert "DEC-recommendation:status" in r2.record["changed_ids"]
    assert clean(root) == []


def test_unchanged_rerun_records_no_material_change(tmp_path):
    root = tmp_path / "d"
    run_pipeline(root, run_id="run-1")
    r2 = run_pipeline(root, run_id="run-2")
    assert r2.record["changed_ids"] == [] and "no material change" in r2.record["supersede_reason"]


def test_older_run_cannot_replace_a_newer_one(tmp_path):
    root = tmp_path / "d"
    run_pipeline(root, run_id="run-1")
    with pytest.raises(history.HistoryError):
        history.guard_current(root, "run-0")
    staging = tmp_path / "stage"
    staging.mkdir()
    with pytest.raises(history.HistoryError):
        history.promote(root, staging, {"run_id": "old"}, None)


# ---------- recovery ----------

def test_interrupted_run_is_preserved_and_recovered(tmp_path, monkeypatch):
    root = tmp_path / "d"
    run_pipeline(root, run_id="run-1")

    def crash(*a, **k):
        raise KeyboardInterrupt("simulated interruption during promotion")
    monkeypatch.setattr(history, "promote", crash)
    with pytest.raises(KeyboardInterrupt):
        run_pipeline(root, run_id="run-2")
    monkeypatch.undo()
    assert (root / history.MARKER).exists() and (root / history.STAGING / "run-2").exists()
    assert history.inspect(root, V, EXT)["interrupted"]["run_id"] == "run-2"

    r3 = run_pipeline(root, run_id="run-3")
    assert r3.status == "partial" and r3.record["recovery"]["attempted"]
    idx = {e["id"]: e for e in history.load_index(root)}
    assert idx["run-2-attempt"]["outcome"] == "interrupted"
    assert (root / "history" / "run-2-attempt" / "event-plan.md").exists()   # partial output kept, not promoted
    assert not (root / history.MARKER).exists() and not (root / history.STAGING).exists()
    assert clean(root) == []


def test_recovery_from_latest_valid_state_after_a_failure(tmp_path, monkeypatch):
    root = tmp_path / "d"
    run_pipeline(root, run_id="run-1")
    monkeypatch.setattr(pipeline, "decide", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("decision boom")))
    r2 = run_pipeline(root, run_id="run-2")
    monkeypatch.undo()
    assert r2.status == "failed" and (root / "failure.json").exists()
    assert not (root / "event-plan.md").exists()              # old outputs are not presented as current
    r3 = run_pipeline(root, run_id="run-3")
    assert r3.status == "partial" and r3.record["supersedes_run_id"] == "run-1"
    outcomes = [(e["id"], e["outcome"]) for e in history.load_index(root)]
    assert ("run-1", "superseded") in outcomes and ("run-2-attempt", "failed") in outcomes
    assert ("run-2", "superseded") in outcomes                # the failure record itself is retained
    assert clean(root) == []


# ---------- failure.json ----------

@pytest.mark.parametrize("target,stage,cls", [
    ("capture_all", "capture", "capture-failure"),
    ("normalize_sources", "normalize", "normalization-failure"),
    ("decide", "decide", "decision-failure"),
])
def test_failure_json_per_stage(tmp_path, monkeypatch, target, stage, cls):
    def boom(*a, **k):
        raise RuntimeError(f"{target} failed")
    monkeypatch.setattr(pipeline, target, boom)
    root = tmp_path / "d"
    r = run_pipeline(root)
    f = json.loads((root / "failure.json").read_text())
    assert (r.status, r.exit_code) == ("failed", 30)
    assert f["affected_stage"] == stage and f["classification"] == cls and f["run_id"] == "run-test-1"
    for key in ("observed_at", "error", "available_evidence", "affected_artifacts", "next_owner", "recovery_action",
                "recovery", "attempt_history_id", "predecessor_run_id"):
        assert key in f, key
    assert f["observed_at"] == FIXED_TIME
    assert json.loads((root / "current-run.json").read_text())["status"] == "failed"
    assert not (root / "snapshots").exists()                  # no completed snapshots are claimed
    if stage != "capture":
        assert f["available_evidence"] and all(e["retrieval_status"] in ("retrieved", "unavailable", "invalid")
                                               for e in f["available_evidence"])
    assert clean(root) == []


def test_render_validation_failure(tmp_path, monkeypatch):
    real = pipeline.render_all

    def broken(ri, out):
        m = real(ri, out)
        m["all_valid"] = False
        m["validation_checks"][0]["outcome"] = "fail"
        return m
    monkeypatch.setattr(pipeline, "render_all", broken)
    root = tmp_path / "d"
    r = run_pipeline(root)
    f = json.loads((root / "failure.json").read_text())
    assert r.status == "failed" and f["classification"] == "render-validation-failure"
    assert any(p.endswith("event-plan.md") for p in f["affected_artifacts"])   # kept in history, not current
    assert not (root / "event-plan.md").exists()


def test_failure_artifacts_contain_no_secrets_or_contacts(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("Authorization: Bearer sk-live-123 api_key=XYZ at /Users/someone/secret mail me@corp.com")
    monkeypatch.setattr(pipeline, "normalize_sources", boom)
    root = tmp_path / "d"
    run_pipeline(root)
    text = (root / "failure.json").read_text() + json.dumps(history.load_index(root))
    for leak in ("sk-live-123", "XYZ", "/Users/someone", "me@corp.com"):
        assert leak not in text, leak


def test_missing_required_snapshot_fact_fails_explicitly(tmp_path):
    from factories import CAL, CAL_H
    cal = xlsx_bytes([CAL_H] + [r for r in CAL if r[0] != "CAL-005"], "Calendar Constraints")
    root = tmp_path / "d"
    r = run_pipeline(root, SRC_CALENDAR=cal)
    f = json.loads((root / "failure.json").read_text())
    assert r.status == "failed" and f["classification"] == "snapshot-failure"
    assert "decision_deadline" in f["error"]["message"]       # not invented


# ---------- determinism, safety ----------

def test_rerun_with_same_inputs_is_byte_identical(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    run_pipeline(a)
    run_pipeline(b)
    files_a = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    assert files_a == sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    for rel in files_a:
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), rel


def test_phase3_4_results_are_unchanged_by_the_pipeline(tmp_path):
    root = tmp_path / "d"
    run_pipeline(root)
    m, _ = decided(tmp_path / "direct", SRC_BRIEF=twelve_demo_brief())
    s6 = snap(root, "feasibility-testing")["state"]["option_results"]
    assert [(o["id"], o["feasibility"], o["costs"]) for o in s6] == \
        [(o["id"], o["feasibility"], o["costs"]) for o in m.options]


def test_no_private_contacts_or_false_confirmation(tmp_path):
    rows = [r + ["Jane Doe, jane@example.com, +886 912 345 678"] for r in ATT]
    root = tmp_path / "d"
    run_pipeline(root, SRC_ATTENDEE=xlsx_bytes([ATT_H + ["contact"]] + rows, "Attendee Signals"))
    for p, t in text_files(root).items():
        assert "Jane" not in t and "jane@example.com" not in t, p
    for name in ("event-plan.md", "draft-communications.md", "vendor-comparison.csv", "event-calendar.ics",
                 "current-run.json"):
        assert affirmative_claims((root / name).read_text()) == [], name


def test_only_registered_source_reads_are_made(tmp_path):
    srcs = load_sources()
    b = bodies(SRC_BRIEF=twelve_demo_brief())
    t = FakeTransport({s["retrieval"]["request_url"]: [ok(b[s["id"]])] for s in srcs})
    run_pipeline(tmp_path / "d", transport=t)
    registered = {s["retrieval"]["request_url"] for s in srcs}
    assert {r.url for r in t.requests} <= registered
    assert {r.method for r in t.requests} <= {"GET", "POST"}
    posts = [r.url for r in t.requests if r.method == "POST"]
    assert posts == ["https://www.notion.so/api/v3/loadPageChunk"]   # Notion's read endpoint only


def test_verify_command(tmp_path):
    import run as run_cli
    root = tmp_path / "d"
    run_pipeline(root)
    assert run_cli.main(["verify", "--deliverables", str(root)]) == 0
    (root / "event-plan.md").write_text("tampered")
    assert run_cli.main(["verify", "--deliverables", str(root)]) == 1
