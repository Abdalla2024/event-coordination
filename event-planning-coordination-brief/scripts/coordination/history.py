"""Current-run pointer, history, interruption detection, archiving and promotion.

Layout under the deliverables root:

    current-run.json            pointer to the active run (written last, so it is the commit point)
    snapshots/ + four drafts + render-manifest.json   the active run's outputs (or failure.json)
    history/index.json          append-only record of every archived run or attempt
    history/<id>/               a retained earlier run or attempt, with archive.json
    .in-progress.json, .staging/<run_id>/   exist only while a run is executing

A run is written to staging and only promoted after it validates, so partially written outputs never
become current. Every earlier state is moved to history, never deleted or overwritten.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .snapshots import STAGES, SNAPSHOT_DIR, snapshot_filename, verify_chain
from .util import atomic_write, dumps, sha256_bytes

CURRENT = "current-run.json"
FAILURE = "failure.json"
MARKER = ".in-progress.json"
STAGING = ".staging"
HISTORY = "history"
INDEX = f"{HISTORY}/index.json"
OUTPUTS = (SNAPSHOT_DIR, "vendor-comparison.csv", "event-plan.md", "event-calendar.ics",
           "draft-communications.md", "render-manifest.json", FAILURE, CURRENT)
RUN_OUTCOMES = ("complete", "partial", "blocked")


class HistoryError(Exception):
    pass


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_index(root: Path) -> list[dict]:
    p = Path(root) / INDEX
    return _read(p) if p.exists() else []


def _append_index(root: Path, entry: dict) -> None:
    entries = load_index(root)
    if any(e["id"] == entry["id"] for e in entries):
        raise HistoryError(f"history entry {entry['id']} already exists")
    atomic_write(Path(root) / INDEX, dumps(entries + [entry]))


def verify_current(root: Path, validator, external) -> list[str]:
    """Check that the active run's files match its pointer and that its snapshot chain is intact."""
    root = Path(root)
    p = root / CURRENT
    if not p.exists():
        return ["no current-run.json"]
    try:
        cur = _read(p)
    except ValueError as exc:
        return [f"current-run.json is not valid JSON ({exc})"]
    problems = []
    for item in cur.get("snapshots", []) + cur.get("artifacts", []):
        f = root / item["path"]
        if not f.exists():
            problems.append(f"{item['path']}: missing")
        elif sha256_bytes(f.read_bytes()) != item["sha256"]:
            problems.append(f"{item['path']}: hash does not match current-run.json")
    if cur.get("status") in RUN_OUTCOMES:
        if len(cur.get("snapshots", [])) != len(STAGES):
            problems.append("current run does not list nine snapshots")
        problems += verify_chain(root, validator, external)
        ids = {json.loads((root / s["path"]).read_text())["run_id"] for s in cur["snapshots"]
               if (root / s["path"]).exists()}
        if ids and ids != {cur["run_id"]}:
            problems.append(f"snapshot run ids {sorted(ids)} do not match current run {cur['run_id']}")
        rm = root / "render-manifest.json"
        if not rm.exists() or not _read(rm).get("all_valid"):
            problems.append("render-manifest.json missing or not all valid")
    elif cur.get("status") == "failed":
        if not (root / FAILURE).exists():
            problems.append("failed run without failure.json")
    else:
        problems.append(f"unknown run status {cur.get('status')!r}")
    return problems


def inspect(root: Path, validator, external) -> dict:
    """Read-only assessment of the deliverables root before a run."""
    root = Path(root)
    marker = root / MARKER
    interrupted = None
    if marker.exists():
        try:
            interrupted = _read(marker)
        except ValueError:
            interrupted = {"run_id": "unknown", "note": "unreadable in-progress marker"}
    present = [n for n in OUTPUTS if (root / n).exists()]
    if (root / CURRENT).exists():
        problems = verify_current(root, validator, external)
        try:
            cur = _read(root / CURRENT)
        except ValueError:
            cur = {}
        state = "valid" if not problems else "invalid"
    elif present:
        cur, problems, state = {}, ["outputs present without current-run.json"], "invalid"
    else:
        cur, problems, state = {}, [], "empty"
    return {"state": state, "current": cur, "problems": problems, "interrupted": interrupted,
            "present": present, "history": load_index(root)}


def _unique_dir(root: Path, base: str) -> tuple[str, Path]:
    hist = Path(root) / HISTORY
    name, n = base, 1
    while (hist / name).exists():
        n += 1
        name = f"{base}-{n}"
    return name, hist / name


def archive_outputs(root: Path, label: str, record: dict) -> str | None:
    """Move the current outputs into history/<label>/ with archive.json. Returns the history id."""
    root = Path(root)
    names = [n for n in OUTPUTS if (root / n).exists()]
    if not names:
        return None
    hid, dest = _unique_dir(root, label)
    dest.mkdir(parents=True)
    for n in names:
        shutil.move(str(root / n), str(dest / n))
    entry = {"id": hid, **record, "path": f"{HISTORY}/{hid}", "files": names}
    atomic_write(dest / "archive.json", dumps(entry))
    _append_index(root, entry)
    return hid


def archive_staging(root: Path, run_id: str, record: dict) -> str | None:
    """Preserve an interrupted or failed attempt's staging directory as history."""
    root = Path(root)
    src = root / STAGING / run_id
    hid, dest = _unique_dir(root, f"{run_id}-attempt")
    dest.mkdir(parents=True)
    files = []
    if src.exists():
        for child in sorted(src.iterdir()):
            shutil.move(str(child), str(dest / child.name))
            files.append(child.name)
        src.rmdir()
    entry = {"id": hid, **record, "path": f"{HISTORY}/{hid}", "files": files}
    atomic_write(dest / "archive.json", dumps(entry))
    _append_index(root, entry)
    return hid


def read_current(root: Path) -> dict:
    p = Path(root) / CURRENT
    try:
        return _read(p) if p.exists() else {}
    except ValueError:
        return {}


def guard_current(root: Path, expected: str | None) -> None:
    live = read_current(root).get("run_id")
    if live != expected:
        raise HistoryError(f"current run changed during this run ({expected} -> {live}); not promoting")


def latest_successful(root: Path) -> dict | None:
    """Latest archived run that completed with complete/partial/blocked status."""
    return next((e for e in reversed(load_index(root))
                 if e.get("outcome") == "superseded" and e.get("status") in RUN_OUTCOMES), None)


def promote(root: Path, staging: Path, pointer: dict, expected_current: str | None) -> None:
    """Move a validated staging run into place and write current-run.json last.

    Refuses if the active run changed since the run started, so an older run can never replace a newer one.
    """
    root = Path(root)
    guard_current(root, expected_current)
    for child in sorted(Path(staging).iterdir()):
        if (root / child.name).exists():
            raise HistoryError(f"{child.name} still present at the root; previous run was not archived")
        shutil.move(str(child), str(root / child.name))
    Path(staging).rmdir()
    atomic_write(root / CURRENT, dumps(pointer))


def verify_history(root: Path, validator, external) -> list[str]:
    """History is append-only, ids unique, superseded runs keep intact chains, snapshot ids never reused."""
    root = Path(root)
    problems, seen_snapshots = [], {}
    entries = load_index(root)
    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        problems.append("duplicate history ids")
    stamps = [e.get("archived_at") or "" for e in entries]
    if stamps != sorted(stamps):
        problems.append("history entries are out of order")
    for e in entries:
        d = root / e["path"]
        if not d.exists():
            problems.append(f"{e['id']}: directory missing")
            continue
        if e.get("outcome") == "superseded" and (d / SNAPSHOT_DIR).exists():
            problems += [f"{e['id']}: {p}" for p in verify_chain(d, validator, external)]
        for s in STAGES:
            f = d / SNAPSHOT_DIR / snapshot_filename(s)
            if f.exists():
                try:
                    sid = json.loads(f.read_text())["snapshot_id"]
                except (ValueError, KeyError):
                    continue
                if sid in seen_snapshots:
                    problems.append(f"snapshot id {sid} appears in {seen_snapshots[sid]} and {e['id']}")
                seen_snapshots[sid] = e["id"]
    if (root / CURRENT).exists():
        cur = _read(root / CURRENT)
        for s in cur.get("snapshots", []):
            if s["snapshot_id"] in seen_snapshots:
                problems.append(f"current snapshot id {s['snapshot_id']} reused from {seen_snapshots[s['snapshot_id']]}")
        sup = cur.get("supersedes_run_id")
        if sup and not any(e.get("run_id") == sup for e in entries):
            problems.append(f"superseded run {sup} is not in history")
    return problems
