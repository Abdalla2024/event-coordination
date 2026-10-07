"""Rendering and packaging: validated Phase 3/4 results -> the four deliverables and a render manifest.

Read-only with respect to everything upstream. It consumes a frozen `RenderInput` and never
retrieves, normalizes, decides or recommends. Values shown come from the decision model, the
recommendation, the programme plan or the validated claims.
"""

from __future__ import annotations

import copy
from pathlib import Path

from ..util import atomic_write, dumps, sha256_bytes
from . import calendar_ics, comms_md, csv_out, impact, plan_md, validate, view
from .cite import Citations
from .view import RenderInput

ARTIFACTS = ("vendor-comparison.csv", "event-plan.md", "event-calendar.ics", "draft-communications.md")
MANIFEST = "render-manifest.json"

__all__ = ["RenderInput", "render_all", "ARTIFACTS", "MANIFEST"]


def _input_hashes(ri: RenderInput) -> dict:
    return {k: sha256_bytes(dumps(getattr(ri, k))) for k in
            ("sources", "claims", "decision", "recommendation", "run_status", "programme")}


def render_all(ri: RenderInput, out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    before = _input_hashes(ri)
    frozen = RenderInput(**{k: copy.deepcopy(getattr(ri, k)) for k in ri.__dataclass_fields__})
    v = view.build(frozen)
    imp = impact.build(frozen)
    plan_text, plan_cited = plan_md.render(v, frozen, imp)
    comms_text, comms_cited = comms_md.render(v, frozen)
    files = {
        "vendor-comparison.csv": csv_out.render(v),
        "event-plan.md": plan_text,
        "event-calendar.ics": calendar_ics.render(v),
        "draft-communications.md": comms_text,
    }
    for name, text in files.items():
        atomic_write(out_dir / name, text.encode("utf-8"))
    known = Citations(frozen).known
    checks = validate.run(frozen, v, files, {"event-plan.md": plan_cited, "draft-communications.md": comms_cited},
                          known)
    after = _input_hashes(ri)
    checks.append({"id": "V-no-mutation", "summary": "Rendering did not change the Phase 3/4 model, claims, "
                   "recommendation, run status or programme", "evidence_ids": [frozen.recommendation["decision"]["id"]],
                   "owner": None, "rationale": None if before == after else "input changed during rendering",
                   "outcome": "pass" if before == after else "fail", "artifact": None, "details": None})
    for name in ARTIFACTS:
        on_disk = (out_dir / name).read_bytes()
        ok = on_disk == files[name].encode("utf-8")
        checks.append({"id": f"V-file-{name}", "summary": f"{name} written and identical to the rendered text",
                       "evidence_ids": [frozen.recommendation["decision"]["id"]], "owner": None,
                       "rationale": None if ok else "file differs", "outcome": "pass" if ok else "fail",
                       "artifact": name, "details": None})
    artifacts = []
    for name in ARTIFACTS:
        data = (out_dir / name).read_bytes()
        failed = [c["id"] for c in checks if c["artifact"] == name and c["outcome"] != "pass"]
        artifacts.append({"id": f"ART-{name.rsplit('.', 1)[0]}", "path": name, "sha256": sha256_bytes(data),
                          "validation_status": "valid" if not failed else "invalid", "failed_checks": failed})
    manifest = {
        "run_id": frozen.run_id, "rendered_at": frozen.rendered_at, "business_clock": frozen.business_clock,
        "run_status": frozen.run_status, "recommendation_status": frozen.recommendation["status"],
        "recommendation": frozen.recommendation["recommendation"],
        "input_sha256": before, "artifacts": artifacts, "validation_checks": checks,
        "all_valid": all(c["outcome"] == "pass" for c in checks),
        "cited_evidence_ids": {"event-plan.md": plan_cited, "draft-communications.md": comms_cited},
        "impact": imp,
        "programme": {"status": frozen.programme["status"], "reason": frozen.programme["reason"],
                      "unallocated_minutes": frozen.programme["unallocated_minutes"]},
    }
    atomic_write(out_dir / MANIFEST, dumps(manifest))
    return manifest
