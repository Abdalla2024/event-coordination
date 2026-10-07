"""Shared claim model for normalized source data.

A *claim* is one normalized business fact. It never carries evidence bytes; it points at the
observations (and, through them, the captured bytes) that support it.

Two separate status fields:

- ``support`` — what the evidence says about the claim:
  ``supported`` (read directly from current evidence), ``unsupported`` (expected but not found, or
  its source was not retrieved), ``conflicting`` (evidence items disagree; no value is chosen),
  ``unresolved`` (evidence exists but cannot be interpreted safely; no value is guessed).
- ``evidence_status`` — the schema retrieval vocabulary applied to the underlying evidence:
  ``retrieved``, ``unavailable``, ``invalid``, ``unverified`` or ``stale``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

SUPPORT = ("supported", "unsupported", "conflicting", "unresolved")
EVIDENCE_STATUS = ("retrieved", "unavailable", "invalid", "unverified", "stale")

WORD_NUMBERS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}


def to_int(text: str) -> int | None:
    t = str(text).strip().lower().replace(",", "")
    if t.isdigit():
        return int(t)
    return WORD_NUMBERS.get(t)


def day_month_year(text: str) -> str | None:
    """'17 October 2026' -> '2026-10-17'. Returns None if the text has no year or does not parse."""
    try:
        return datetime.strptime(text.strip(), "%d %B %Y").date().isoformat()
    except ValueError:
        return None


@dataclass
class Claim:
    id: str
    kind: str
    summary: str
    value: object = None
    support: str = "supported"
    evidence_status: str = "retrieved"
    evidence_ids: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    owner: str | None = None
    rationale: str | None = None
    provenance: list[dict] = field(default_factory=list)
    fields: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.support not in SUPPORT:
            raise ValueError(f"{self.id}: unknown support {self.support!r}")
        if self.evidence_status not in EVIDENCE_STATUS:
            raise ValueError(f"{self.id}: unknown evidence_status {self.evidence_status!r}")
        if self.support != "supported" and self.value is not None:
            raise ValueError(f"{self.id}: a {self.support} claim cannot carry a chosen value; "
                             "keep candidate or raw values in fields")
        if self.support == "supported" and not self.evidence_ids:
            raise ValueError(f"{self.id}: a supported claim needs evidence")

    def as_record(self) -> dict:
        return {"id": self.id, "summary": self.summary, "evidence_ids": list(dict.fromkeys(self.evidence_ids)),
                "owner": self.owner, "rationale": self.rationale, "kind": self.kind,
                "support": self.support, "evidence_status": self.evidence_status, "value": self.value,
                "source_ids": list(dict.fromkeys(self.source_ids)), "provenance": self.provenance,
                **self.fields}


class ObservationIndex:
    """Observation id -> provenance (source, locator, retrieval timestamp, native version)."""

    def __init__(self, captured: dict):
        self.obs: dict[str, dict] = {}
        self.sources: dict[str, dict] = {}
        for sid, c in captured.items():
            rec = c.record
            self.sources[sid] = rec
            for o in rec["observations"]:
                self.obs[o["id"]] = {"source_id": sid, "observation": o}

    def provenance(self, obs_ids) -> list[dict]:
        out = []
        for oid in obs_ids:
            if oid not in self.obs:
                continue
            sid = self.obs[oid]["source_id"]
            rec = self.sources[sid]
            out.append({"observation_id": oid, "source_id": sid,
                        "locator": self.obs[oid]["observation"]["locator"],
                        "retrieved_at": rec["retrieved_at"],
                        "native_version": rec["version_metadata"].get("native_version")})
        return out


def unavailable_claim(cid: str, kind: str, what: str, sid: str, status: str) -> Claim:
    """Placeholder for an expected claim whose source was not retrieved or could not be interpreted."""
    support = "unsupported" if status == "unavailable" else "unresolved"
    return Claim(cid, kind, f"{what}: withheld because source {sid} is '{status}'.",
                 None, support, status if status != "retrieved" else "invalid",
                 [sid, "ASG-TRACE"], [sid],
                 rationale="Dependent claims are withheld; nothing is substituted.")


def table_usable(captured, sid: str) -> tuple[bool, str]:
    """A table source is usable when retrieved and its table was interpretable (not held)."""
    c = captured.get(sid)
    if c is None:
        return False, "unavailable"
    status = c.record["retrieval_status"]
    if status != "retrieved" or c.parsed is None:
        return False, status
    if getattr(c.parsed, "held", False):
        return False, "invalid"
    return True, status


def issue_index(captured, sid: str) -> dict[str, list[dict]]:
    """Row-level parse issues keyed by the affected record id."""
    out: dict[str, list[dict]] = {}
    c = captured.get(sid)
    for iss in (c.record.get("parse_issues", []) if c else []):
        for rid in iss.get("affected_ids", []):
            out.setdefault(rid, []).append(iss)
    return out


def held_claims(captured, sid: str, prefix: str, kind: str) -> list[Claim]:
    """One claim per row-level issue: duplicates are conflicting, invalid rows unresolved."""
    out = []
    for rid, issues in issue_index(captured, sid).items():
        kinds = {i["kind"] for i in issues}
        support = "conflicting" if "duplicate-id" in kinds else "unresolved"
        status = "unverified" if support == "conflicting" else "invalid"
        out.append(Claim(f"{prefix}-{rid}", kind,
                         f"{rid}: held, " + "; ".join(i["summary"] for i in issues),
                         None, support, status, [i["id"] for i in issues], [sid],
                         rationale="Held before dependent interpretation (ASG-CHANGED-INPUTS).",
                         fields={"record_key": rid, "issue_kinds": sorted(kinds)}))
    return out


def parse_hhmm(text: str) -> str:
    h, m = text.split(":")
    return f"{int(h):02d}:{int(m):02d}"


def iso_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
