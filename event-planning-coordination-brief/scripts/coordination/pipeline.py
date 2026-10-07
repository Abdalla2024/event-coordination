"""End-to-end run: capture -> normalize -> decide -> recommend -> programme -> render -> nine snapshots.

Orchestration only. Each step calls the existing phase entry point; no business rule lives here.
The run is built in `.staging/<run_id>/` and promoted only after every validation passes; earlier
states are moved to history, never deleted. Any failure leaves `failure.json` and an auditable
history entry, and old outputs are never presented as the current result.

Read-only towards every source system: it only performs the registered HTTP reads.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import history, stages
from .config import load_config, load_requirements_evidence, load_sources
from .decide import decide
from .normalize import normalize_sources
from .programme import plan as programme_plan
from .recommend import recommend, run_status
from .render import RenderInput, render_all
from .snapshots import SnapshotChain, load_validator, new_run_id, verify_chain
from .sources import capture_all
from .util import atomic_write, dumps, sha256_bytes, utc_now

EXIT_CODES = {"complete": 0, "partial": 10, "blocked": 20, "failed": 30}
NEXT_OWNER = "Event and Operations Manager"   # the stakeholder who runs the planning package (STK-I1-L13)
CLASSIFICATION = {
    "preflight": "recovery-failure", "capture": "capture-failure", "normalize": "normalization-failure",
    "decide": "decision-failure", "recommend": "decision-failure", "programme": "programme-failure",
    "render": "render-validation-failure", "snapshots": "snapshot-failure", "verify": "snapshot-failure",
    "promote": "publication-failure",
}
REDACT = (
    (re.compile(r"(?i)bearer\s+\S+"), "Bearer [redacted]"),
    (re.compile(r"(?i)(authorization|api[_-]?key|token|password|secret|cookie)\s*[:=]\s*\S+"), r"\1: [redacted]"),
    (re.compile(r"/(Users|home)/[^/\s]+"), "~"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}"), "[email redacted]"),
)


class StageFailure(Exception):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


@dataclass
class RunResult:
    run_id: str
    status: str
    exit_code: int
    record: dict
    root: Path


def sanitize(text: str, limit: int = 500) -> str:
    for rx, repl in REDACT:
        text = rx.sub(repl, text)
    return text[:limit]


def build_render_input(run_id, cfg, results, normalized, model, rec, status, completed_at) -> RenderInput:
    """Plain-data snapshot of the validated model for the renderers (a JSON round trip, so nothing shared)."""
    plain = lambda x: json.loads(dumps(x))  # noqa: E731
    decision = plain(model.as_dict())
    claims = plain(normalized.as_records())
    return RenderInput(run_id=run_id, rendered_at=completed_at, business_clock=cfg.raw["business_clock"],
                       sources=plain([r.record for r in results.values()]), claims=claims, decision=decision,
                       recommendation=plain(rec.as_dict()), run_status=plain(status),
                       programme=programme_plan(decision, claims))


def fingerprint(source: dict) -> str:
    """Hash of what was read from a source (its observations and status), not of its raw bytes.

    Raw bytes can differ between identical downloads (spreadsheet export timestamps, a page's rotating
    event list), so material change is judged on the interpreted observations.
    """
    obs = [{k: o.get(k) for k in ("id", "summary", "values", "value", "text", "locator")} for o in source["observations"]]
    return sha256_bytes(dumps({"status": source["retrieval_status"], "observations": obs}))


def _changes(previous: dict, sources: list[dict], rec: dict, decision: dict) -> list[str]:
    """Source ids whose interpreted content changed, and decision ids whose outcome changed, versus the prior run."""
    if not previous:
        return []
    prev_fp = previous.get("source_fingerprints", {})
    changed = [s["id"] for s in sources if prev_fp.get(s["id"]) != fingerprint(s)]
    prev_opts = previous.get("decision_summary", {}).get("options", {})
    changed += [f"{o['id']}:feasibility" for o in decision["options"] if prev_opts.get(o["id"]) != o["feasibility"]]
    changed += [f"{o}:removed" for o in prev_opts if o not in {x["id"] for x in decision["options"]}]
    if previous.get("decision_summary", {}).get("recommendation_status") != rec["status"]:
        changed.append("DEC-recommendation:status")
    return changed


def execute(root: Path | None = None, *, transport, clock=utc_now, run_id: str | None = None,
            sources: list[dict] | None = None, floorplan_file: Path | None = None) -> RunResult:
    """Run the whole workflow into `root` (default: the configured deliverables directory).

    `clock`, `run_id`, `sources` and `floorplan_file` exist for deterministic tests; live runs use defaults.
    """
    cfg = load_config()
    root = Path(root or cfg.deliverables_dir)
    root.mkdir(parents=True, exist_ok=True)
    validator = load_validator(cfg.schema_path)
    external = set(load_requirements_evidence())
    run_id = run_id or new_run_id()
    started = clock()
    stage = "preflight"
    staging = root / history.STAGING / run_id
    recovery = {"attempted": False, "prior_state": None, "actions": [], "outcome": None}
    previous_valid: dict = {}
    expected_current = None
    captured = None
    try:
        # -- preflight and recovery --------------------------------------------------------------
        pre = history.inspect(root, validator, external)
        recovery["prior_state"] = pre["state"]
        if pre["interrupted"]:
            recovery["attempted"] = True
            rid = pre["interrupted"].get("run_id", "unknown")
            hid = history.archive_staging(root, rid, {
                "run_id": rid, "outcome": "interrupted", "archived_at": clock(),
                "reason": "an earlier run did not finish; its partial outputs were never promoted",
                "detected_by": run_id})
            (root / history.MARKER).unlink()
            recovery["actions"].append(f"preserved interrupted attempt {rid} as history/{hid}")
        if pre["state"] == "valid":
            expected_current = pre["current"]["run_id"]
            if pre["current"].get("status") in history.RUN_OUTCOMES:
                previous_valid = pre["current"]
            else:  # the current state is a recorded failure: compare against the latest successful run
                last = history.latest_successful(root)
                previous_valid = {"run_id": last["run_id"], **last.get("pointer", {})} if last else {}
                recovery["attempted"] = True
                recovery["actions"].append(f"current state is failed run {expected_current}; "
                                           + (f"latest successful run is {last['run_id']}" if last else
                                              "no earlier successful run exists"))
        elif pre["state"] == "invalid":
            recovery["attempted"] = True
            cur = pre["current"]
            label = cur.get("run_id") or f"unindexed-{started.replace(':', '').replace('.', '')}"
            hid = history.archive_outputs(root, label, {
                "run_id": cur.get("run_id"), "outcome": "invalid", "archived_at": clock(),
                "reason": "current outputs failed verification: " + "; ".join(pre["problems"])[:800],
                "status": cur.get("status"), "superseded_by": run_id})
            recovery["actions"].append(f"preserved invalid current outputs as history/{hid}")
            last = history.latest_successful(root)
            if last:
                previous_valid = {"run_id": last["run_id"], **last.get("pointer", {})}
                recovery["actions"].append(f"latest valid state is {last['run_id']} in history")
        recovery["outcome"] = "recovered" if recovery["attempted"] else "not needed"
        atomic_write(root / history.MARKER, dumps({"run_id": run_id, "started_at": started}))
        staging.mkdir(parents=True, exist_ok=True)

        # -- phases (existing entry points) ----------------------------------------------------
        stage = "capture"
        captured = capture_all(sources or load_sources(), cfg.http_profiles, transport, staging,
                               clock=None if clock is utc_now else clock)
        stage = "normalize"
        normalized = normalize_sources(captured, cfg.business_clock, floorplan_file)
        stage = "decide"
        model = decide(normalized, cfg.business_clock)
        stage = "recommend"
        rec = recommend(model, normalized)
        status = run_status([c.record for c in captured.values()], model, rec)
        stage = "programme"
        ri = build_render_input(run_id, cfg, captured, normalized, model, rec, status, clock())
        stage = "render"
        manifest = render_all(ri, staging)
        if not manifest["all_valid"]:
            bad = [c["id"] for c in manifest["validation_checks"] if c["outcome"] != "pass"]
            raise StageFailure("render", f"deliverable validation failed: {bad}")

        # -- snapshots ------------------------------------------------------------------------
        stage = "snapshots"
        changed = _changes(previous_valid, ri.sources, ri.recommendation, ri.decision)
        sup_id = previous_valid.get("run_id")
        reason = ("first run; nothing superseded" if not sup_id else
                  f"supersedes {sup_id}: " + (f"material change in {changed}" if changed else
                                              "no material change; re-captured and re-verified"))
        chain = SnapshotChain(staging, run_id, validator, cfg.schema_version, external, clock=clock)
        entries = stages.build(chain, {"sources": ri.sources, "claims": ri.claims, "decision": ri.decision,
                                       "recommendation": ri.recommendation, "run_status": ri.run_status,
                                       "programme": ri.programme, "render_manifest": manifest,
                                       "supersede": {"supersedes_run_id": sup_id, "changed_ids": changed,
                                                     "reason": reason, "recovery": recovery}})
        stage = "verify"
        problems = verify_chain(staging, validator, external)
        if problems:
            raise StageFailure("verify", f"snapshot chain invalid: {problems[:5]}")

        # -- promote ----------------------------------------------------------------------------
        stage = "promote"
        completed = clock()
        pointer = {
            "run_id": run_id, "status": status["status"], "status_reasons": status["reasons"],
            "started_at": started, "completed_at": completed, "business_clock": cfg.raw["business_clock"],
            "supersedes_run_id": sup_id, "supersede_reason": reason, "changed_ids": changed, "recovery": recovery,
            "snapshots": entries,
            "artifacts": [{"path": a["path"], "sha256": a["sha256"]} for a in manifest["artifacts"]],
            "source_hashes": {s["id"]: s["content_hash"] for s in ri.sources},
            "source_fingerprints": {s["id"]: fingerprint(s) for s in ri.sources},
            "source_status": {s["id"]: s["retrieval_status"] for s in ri.sources},
            "decision_summary": {"options": {o["id"]: o["feasibility"] for o in ri.decision["options"]},
                                 "recommendation_status": rec.status, "recommendation": rec.recommendation},
            "exit_code": EXIT_CODES[status["status"]], "failure": None,
        }
        history.guard_current(root, expected_current)   # an older run never replaces a newer one
        if expected_current:
            prior = history.read_current(root)
            history.archive_outputs(root, expected_current, {
                "run_id": expected_current, "outcome": "superseded", "archived_at": completed,
                "reason": reason, "status": prior.get("status"), "superseded_by": run_id,
                "pointer": {k: prior.get(k) for k in ("status", "source_hashes", "source_fingerprints", "decision_summary")}})
        history.promote(root, staging, pointer, None)
        after = history.verify_current(root, validator, external) + history.verify_history(root, validator, external)
        if after:
            raise StageFailure("promote", f"post-promotion verification failed: {after[:5]}")
        (root / history.MARKER).unlink()
        _cleanup_staging(root)
        return RunResult(run_id, status["status"], EXIT_CODES[status["status"]], pointer, root)
    except Exception as exc:  # every failure is recorded; nothing is downgraded to success
        return _fail(root, run_id, stage, exc, started, clock, recovery, previous_valid, expected_current, captured)


def _cleanup_staging(root: Path) -> None:
    s = root / history.STAGING
    if s.exists() and not any(s.iterdir()):
        s.rmdir()


def _fail(root, run_id, stage, exc, started, clock, recovery, previous_valid, expected_current, captured) -> RunResult:
    stage = getattr(exc, "stage", stage)
    observed = clock()
    evidence = []
    if captured:
        for sid, c in captured.items():
            for a in c.record["attempts"]:
                evidence.append({"source_id": sid, "attempt_id": a["id"], "outcome": a["outcome"],
                                 "retrieval_status": c.record["retrieval_status"]})
    staged = sorted(p.name for p in (root / history.STAGING / run_id).glob("*")) \
        if (root / history.STAGING / run_id).exists() else []
    attempt_id = history.archive_staging(root, run_id, {
        "run_id": run_id, "outcome": "failed", "archived_at": observed, "stage": stage,
        "reason": f"{type(exc).__name__}: {sanitize(str(exc), 300)}"})
    superseded = None
    if expected_current and history.read_current(root).get("run_id") == expected_current:
        prior = history.read_current(root)
        superseded = history.archive_outputs(root, expected_current, {
            "run_id": expected_current, "outcome": "superseded", "archived_at": observed,
            "reason": f"superseded by failed run {run_id}; earlier outputs are not presented as current",
            "status": prior.get("status"), "superseded_by": run_id,
            "pointer": {k: prior.get(k) for k in ("status", "source_hashes", "source_fingerprints", "decision_summary")}})
    elif (root / history.CURRENT).exists() or any((root / n).exists() for n in history.OUTPUTS):
        superseded = history.archive_outputs(root, f"pre-{run_id}", {
            "run_id": None, "outcome": "invalid", "archived_at": observed,
            "reason": f"outputs present when run {run_id} failed", "superseded_by": run_id})
    failure = {
        "run_id": run_id, "observed_at": observed, "started_at": started, "status": "failed",
        "affected_stage": stage, "classification": CLASSIFICATION.get(stage, "unknown-failure"),
        "error": {"type": type(exc).__name__, "message": sanitize(str(exc))},
        "current_run_before": expected_current, "predecessor_run_id": previous_valid.get("run_id"),
        "available_evidence": evidence,
        "affected_artifacts": [f"history/{attempt_id}/{n}" for n in staged],
        "attempt_history_id": attempt_id, "superseded_history_id": superseded,
        "recovery": {**recovery, "failed_run_preserved_as": f"history/{attempt_id}"},
        "next_owner": NEXT_OWNER,
        "recovery_action": ("Resolve the cause recorded in 'error', then run the end-to-end command again; the "
                            "failed attempt and earlier runs are preserved in history."),
    }
    atomic_write(root / history.FAILURE, dumps(failure))
    pointer = {"run_id": run_id, "status": "failed", "started_at": started, "completed_at": observed,
               "supersedes_run_id": previous_valid.get("run_id"), "snapshots": [], "artifacts": [],
               "failure": history.FAILURE, "recovery": failure["recovery"], "exit_code": EXIT_CODES["failed"]}
    atomic_write(root / history.CURRENT, dumps(pointer))
    marker = root / history.MARKER
    if marker.exists():
        marker.unlink()
    _cleanup_staging(root)
    return RunResult(run_id, "failed", EXIT_CODES["failed"], pointer, root)
