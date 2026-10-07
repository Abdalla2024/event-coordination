"""Runtime configuration: paths, business clock, source registry, evidence references."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILL_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@dataclass(frozen=True)
class RunConfig:
    raw: dict
    business_clock: datetime
    business_timezone: str
    schema_path: Path
    schema_version: str
    deliverables_dir: Path
    http_timeout: float
    http_profiles: dict

    @property
    def currency(self) -> str:
        return self.raw["currency"]


def load_config(repo_root: Path = REPO_ROOT) -> RunConfig:
    raw = _load_json(REFERENCES_DIR / "run-config.json")
    clock = datetime.fromisoformat(raw["business_clock"])
    if clock.tzinfo is None:
        raise ValueError("business_clock must carry an explicit UTC offset")
    return RunConfig(
        raw=raw,
        business_clock=clock,
        business_timezone=raw["business_timezone"],
        schema_path=repo_root / raw["schema_path"],
        schema_version=raw["schema_version"],
        deliverables_dir=repo_root / raw["deliverables_dir"],
        http_timeout=float(raw["http"]["timeout_seconds"]),
        http_profiles=raw["http"]["profiles"],
    )


def load_sources() -> list[dict]:
    sources = _load_json(REFERENCES_DIR / "sources.json")["sources"]
    ids = [s["id"] for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source id in references/sources.json")
    return sources


def load_requirements_evidence() -> dict:
    """STK-* and ASG-* evidence records, keyed by id."""
    data = _load_json(REFERENCES_DIR / "requirements-evidence.json")
    out = {}
    for group in ("stakeholder", "assignment"):
        for rec in data[group]:
            if rec["id"] in out:
                raise ValueError(f"duplicate evidence id {rec['id']}")
            out[rec["id"]] = {**rec, "group": group}
    return out
