#!/usr/bin/env python3
"""Entry point for the event-planning-coordination-brief skill.

Phase 1 provides the `capture` command: retrieve every disclosed source, record every attempt,
parse what was retrieved, and write a capture report. Later phases add the full nine-stage run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coordination.config import load_config, load_sources  # noqa: E402
from coordination.decide import decide  # noqa: E402
from coordination.normalize import normalize_sources  # noqa: E402
from coordination.recommend import recommend, run_status  # noqa: E402
from coordination.snapshots import new_run_id  # noqa: E402
from coordination.sources import capture_all  # noqa: E402
from coordination.transport import urllib_transport  # noqa: E402
from coordination.util import atomic_write, dumps, utc_now  # noqa: E402


def cmd_capture(args) -> int:
    cfg = load_config()
    out = Path(args.out).resolve()
    run_id = new_run_id()
    started = utc_now()
    results = capture_all(load_sources(), cfg.http_profiles, urllib_transport(cfg.http_timeout), out)
    report = {
        "run_id": run_id,
        "command": "capture",
        "started_at": started,
        "completed_at": utc_now(),
        "business_clock": cfg.raw["business_clock"],
        "sources": [r.record for r in results.values()],
    }
    atomic_write(out / "capture-report.json", dumps(report))
    for sid, r in results.items():
        attempts = ", ".join(f"{a.profile}:{a.outcome}" for a in r.capture.attempts)
        print(f"{sid:16} {r.record['retrieval_status']:11} obs={len(r.record['observations']):3} "
              f"issues={len(r.issues)}  [{attempts}]")
    print(f"report: {out / 'capture-report.json'}")
    return 0 if all(r.record["retrieval_status"] == "retrieved" for r in results.values()) else 2


def cmd_normalize(args) -> int:
    cfg = load_config()
    out = Path(args.out).resolve()
    started = utc_now()
    results = capture_all(load_sources(), cfg.http_profiles, urllib_transport(cfg.http_timeout), out)
    normalized = normalize_sources(results, cfg.business_clock)
    report = {
        "run_id": new_run_id(),
        "command": "normalize",
        "started_at": started,
        "completed_at": utc_now(),
        "business_clock": cfg.raw["business_clock"],
        "sources": [r.record for r in results.values()],
        "normalized_summary": normalized.summary(),
        "claims": normalized.as_records(),
    }
    atomic_write(out / "normalized-report.json", dumps(report))
    s = normalized.summary()
    print(f"claims: {s['claims']}  support: {s['by_support']}  evidence: {s['by_evidence_status']}")
    for c in normalized.not_supported():
        print(f"  {c.support:11} {c.id}: {c.summary[:150]}")
    print(f"report: {out / 'normalized-report.json'}")
    return 0


def _decision_pipeline(out: Path):
    cfg = load_config()
    results = capture_all(load_sources(), cfg.http_profiles, urllib_transport(cfg.http_timeout), out)
    normalized = normalize_sources(results, cfg.business_clock)
    return cfg, results, normalized, decide(normalized, cfg.business_clock)


def _print_options(model) -> None:
    for o in model.options:
        c = o["costs"]
        total = c["total_with_allowances_twd"] if c["complete"] else f"blank ({c['incomplete_reason']})"
        print(f"{o['feasibility']:12} {o['id']:34} total={total}")


def cmd_decide(args) -> int:
    out = Path(args.out).resolve()
    started = utc_now()
    cfg, results, normalized, model = _decision_pipeline(out)
    report = {
        "run_id": new_run_id(),
        "command": "decide",
        "started_at": started,
        "completed_at": utc_now(),
        "business_clock": cfg.raw["business_clock"],
        "sources": [r.record for r in results.values()],
        "claims": normalized.as_records(),
        "decision": model.as_dict(),
        "decision_summary": model.summary(),
    }
    atomic_write(out / "decision-report.json", dumps(report))
    _print_options(model)
    for u in model.unresolved:
        print(f"unresolved  {u['id']}: {u['summary'][:140]}")
    print(f"report: {out / 'decision-report.json'}")
    return 0


def cmd_recommend(args) -> int:
    out = Path(args.out).resolve()
    started = utc_now()
    cfg, results, normalized, model = _decision_pipeline(out)
    rec = recommend(model, normalized)
    status = run_status([r.record for r in results.values()], model, rec)
    report = {
        "run_id": new_run_id(),
        "command": "recommend",
        "started_at": started,
        "completed_at": utc_now(),
        "business_clock": cfg.raw["business_clock"],
        "sources": [r.record for r in results.values()],
        "claims": normalized.as_records(),
        "decision": model.as_dict(),
        "recommendation": rec.as_dict(),
        "run_status": status,
    }
    atomic_write(out / "recommendation-report.json", dumps(report))
    _print_options(model)
    print(f"recommendation: {rec.status} -> {rec.recommendation}")
    if rec.question_for_operations:
        print(f"  {rec.question_for_operations}")
    print(f"run status: {status['status']} ({'; '.join(status['reasons'])})")
    print(f"report: {out / 'recommendation-report.json'}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("capture", help="retrieve and parse every disclosed source")
    c.add_argument("--out", required=True, help="output root; evidence goes to <out>/snapshots/evidence")
    c.set_defaults(func=cmd_capture)
    n = sub.add_parser("normalize", help="capture, then normalize every source into evidence-linked claims")
    n.add_argument("--out", required=True, help="output root; evidence goes to <out>/snapshots/evidence")
    n.set_defaults(func=cmd_normalize)
    d = sub.add_parser("decide", help="capture, normalize, then build the feasibility model (no deliverables)")
    d.add_argument("--out", required=True, help="output root; evidence goes to <out>/snapshots/evidence")
    d.set_defaults(func=cmd_decide)
    r = sub.add_parser("recommend", help="decide, then compare non-infeasible options (no deliverables)")
    r.add_argument("--out", required=True, help="output root; evidence goes to <out>/snapshots/evidence")
    r.set_defaults(func=cmd_recommend)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
