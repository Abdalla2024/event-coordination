"""Nine-stage snapshot chain: ordering, predecessor hashes, record-id bookkeeping, schema validation.

`SnapshotChain.write` refuses to write a snapshot that would break the chain. `verify_chain` re-reads
the files from disk and checks the same rules independently, for publication validation and reruns.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from jsonschema import Draft202012Validator, FormatChecker

from .util import atomic_write, dumps, sha256_bytes, utc_now

STAGES = (
    "scope-and-approval-gates",
    "source-capture",
    "constraint-model",
    "planning-baseline",
    "option-generation",
    "feasibility-testing",
    "decision-and-approval",
    "draft-propagation",
    "publication-validation",
)
SNAPSHOT_DIR = "snapshots"


class ChainError(Exception):
    pass


def snapshot_filename(stage: str) -> str:
    return f"{STAGES.index(stage) + 1:02d}-{stage}.json"


def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return f"run-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"


def load_validator(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def collect_ids(node) -> set[str]:
    """Every record id defined anywhere inside a snapshot document."""
    found: set[str] = set()
    if isinstance(node, dict):
        if isinstance(node.get("id"), str):
            found.add(node["id"])
        for v in node.values():
            found |= collect_ids(v)
    elif isinstance(node, list):
        for v in node:
            found |= collect_ids(v)
    return found


def collect_evidence_refs(node) -> set[str]:
    refs: set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "evidence_ids" and isinstance(v, list):
                refs |= {x for x in v if isinstance(x, str)}
            else:
                refs |= collect_evidence_refs(v)
    elif isinstance(node, list):
        for v in node:
            refs |= collect_evidence_refs(v)
    return refs


def schema_errors(validator: Draft202012Validator, doc: dict) -> list[str]:
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))]


class SnapshotChain:
    def __init__(self, deliverables_root: Path, run_id: str, validator: Draft202012Validator,
                 schema_version: str, external_evidence: Iterable[str],
                 clock: Callable[[], str] = utc_now):
        self.root = Path(deliverables_root)
        self.run_id = run_id
        self.validator = validator
        self.schema_version = schema_version
        self.external = set(external_evidence)
        self.clock = clock
        self.written: list[dict] = []          # {"stage","snapshot_id","path","sha256"}
        self.produced: set[str] = set()        # record ids produced by earlier snapshots
        self.defined: set[str] = set()         # every id defined in earlier snapshots

    @property
    def next_stage(self) -> str | None:
        return STAGES[len(self.written)] if len(self.written) < len(STAGES) else None

    def write(self, stage: str, status: str, state: dict, consumed: list[str], produced: list[str],
              unresolved: list[dict] | None = None, decisions: list[dict] | None = None,
              extra: dict | None = None) -> dict:
        if stage != self.next_stage:
            raise ChainError(f"expected stage {self.next_stage!r}, got {stage!r}")
        clash = set(extra or {}) & {"schema_version", "snapshot_id", "run_id", "stage", "sequence",
                                    "created_at", "status", "predecessor", "consumed_record_ids",
                                    "produced_record_ids", "state", "unresolved", "decisions"}
        if clash:
            raise ChainError(f"extra fields may not override snapshot fields: {sorted(clash)}")
        seq = len(self.written) + 1
        prev = self.written[-1] if self.written else None
        doc = {
            "schema_version": self.schema_version,
            "snapshot_id": f"{self.run_id}-s{seq:02d}",
            "run_id": self.run_id,
            "stage": stage,
            "sequence": seq,
            "created_at": self.clock(),
            "status": status,
            "predecessor": None if prev is None else {
                "snapshot_id": prev["snapshot_id"], "path": prev["path"], "sha256": prev["sha256"]},
            "consumed_record_ids": list(consumed),
            "produced_record_ids": list(produced),
            "state": state,
            "unresolved": unresolved or [],
            "decisions": decisions or [],
            **(extra or {}),
        }
        problems = schema_errors(self.validator, doc)
        problems += self._chain_problems(doc)
        if problems:
            raise ChainError(f"snapshot {seq:02d} {stage} rejected:\n  " + "\n  ".join(problems))
        rel = f"{SNAPSHOT_DIR}/{snapshot_filename(stage)}"
        data = dumps(doc)
        atomic_write(self.root / rel, data)
        entry = {"stage": stage, "snapshot_id": doc["snapshot_id"], "path": rel, "sha256": sha256_bytes(data)}
        self.written.append(entry)
        self.produced |= set(produced)
        self.defined |= collect_ids(doc)
        return entry

    def _chain_problems(self, doc: dict) -> list[str]:
        out = []
        consumed, produced = doc["consumed_record_ids"], doc["produced_record_ids"]
        unknown = [c for c in consumed if c not in self.produced]
        if unknown:
            out.append(f"consumed ids not produced by an earlier snapshot: {unknown}")
        reproduced = [p for p in produced if p in self.produced]
        if reproduced:
            out.append(f"ids already produced earlier in this run: {reproduced}")
        here = collect_ids(doc["state"]) | collect_ids(doc["unresolved"]) | collect_ids(doc["decisions"])
        missing = [p for p in produced if p not in here]
        if missing:
            out.append(f"produced ids not defined in this snapshot: {missing}")
        known = self.external | self.defined | collect_ids(doc)
        dangling = sorted(collect_evidence_refs(doc) - known)
        if dangling:
            out.append(f"evidence ids that do not resolve: {dangling}")
        return out


def verify_chain(deliverables_root: Path, validator: Draft202012Validator,
                 external_evidence: Iterable[str]) -> list[str]:
    """Independently re-check the nine snapshots on disk. Returns a list of problems (empty = valid)."""
    root, external = Path(deliverables_root), set(external_evidence)
    problems: list[str] = []
    prev_entry, run_id = None, None
    produced, defined, snapshot_ids = set(), set(), set()
    for seq, stage in enumerate(STAGES, start=1):
        rel = f"{SNAPSHOT_DIR}/{snapshot_filename(stage)}"
        path = root / rel
        if not path.exists():
            problems.append(f"{rel}: missing")
            prev_entry = None
            continue
        data = path.read_bytes()
        try:
            doc = json.loads(data)
        except ValueError as exc:
            problems.append(f"{rel}: not valid JSON ({exc})")
            prev_entry = None
            continue
        problems += [f"{rel}: {e}" for e in schema_errors(validator, doc)]
        if doc.get("stage") != stage or doc.get("sequence") != seq:
            problems.append(f"{rel}: stage/sequence mismatch")
        run_id = run_id or doc.get("run_id")
        if doc.get("run_id") != run_id:
            problems.append(f"{rel}: run_id {doc.get('run_id')} differs from {run_id}")
        if doc.get("snapshot_id") in snapshot_ids:
            problems.append(f"{rel}: duplicate snapshot_id")
        snapshot_ids.add(doc.get("snapshot_id"))
        pred = doc.get("predecessor")
        if seq > 1:
            if prev_entry is None:
                problems.append(f"{rel}: predecessor cannot be checked (previous snapshot unreadable)")
            elif pred != prev_entry:
                problems.append(f"{rel}: predecessor {pred} does not match {prev_entry}")
        unknown = [c for c in doc.get("consumed_record_ids", []) if c not in produced]
        if unknown:
            problems.append(f"{rel}: consumed ids not produced earlier: {unknown}")
        ids_here = collect_ids(doc)
        missing = [p for p in doc.get("produced_record_ids", []) if p not in ids_here]
        if missing:
            problems.append(f"{rel}: produced ids not defined: {missing}")
        dangling = sorted(collect_evidence_refs(doc) - (external | defined | ids_here))
        if dangling:
            problems.append(f"{rel}: unresolved evidence ids: {dangling}")
        produced |= set(doc.get("produced_record_ids", []))
        defined |= ids_here
        prev_entry = {"snapshot_id": doc.get("snapshot_id"), "path": rel, "sha256": sha256_bytes(data)}
    return problems
