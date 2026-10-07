"""Normalization: captured and parsed sources -> evidence-linked business claims.

Entry point: ``normalize_sources(captured, clock)``. Read-only: it only reads captured records and
reference files; it never contacts a vendor, venue, calendar or person.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import attendee, brief, budget, calendar, crosscheck, prerequisites, vendor, venue
from .base import Claim, ObservationIndex


@dataclass
class NormalizedSources:
    claims: list[Claim]

    def __post_init__(self):
        ids = Counter(c.id for c in self.claims)
        dup = [i for i, n in ids.items() if n > 1]
        if dup:
            raise ValueError(f"duplicate claim ids: {dup}")
        self.by_id = {c.id: c for c in self.claims}

    def get(self, cid: str) -> Claim | None:
        return self.by_id.get(cid)

    def of_kind(self, kind: str) -> list[Claim]:
        return [c for c in self.claims if c.kind == kind]

    def not_supported(self) -> list[Claim]:
        return [c for c in self.claims if c.support != "supported"]

    def summary(self) -> dict:
        return {"claims": len(self.claims),
                "by_support": dict(Counter(c.support for c in self.claims)),
                "by_evidence_status": dict(Counter(c.evidence_status for c in self.claims)),
                "by_kind": dict(Counter(c.kind for c in self.claims))}

    def as_records(self) -> list[dict]:
        return [c.as_record() for c in self.claims]


def normalize_sources(captured: dict, clock: datetime, floorplan_file: Path | None = None) -> NormalizedSources:
    claims: list[Claim] = []
    claims += calendar.normalize(captured, clock)
    claims += budget.normalize(captured)
    claims += attendee.normalize(captured, clock)
    claims += vendor.normalize(captured, clock)
    claims += brief.normalize(captured)
    claims += venue.normalize(captured, floorplan_file)
    cs = crosscheck.Claims(claims)
    claims += crosscheck.run(cs, clock)
    claims += prerequisites.run(crosscheck.Claims(claims))
    index = ObservationIndex(captured)
    by_id = {c.id: c for c in claims}

    def observations(ids, seen):
        """Follow claim-to-claim evidence down to source observations."""
        out = []
        for i in ids:
            if i in index.obs:
                out.append(i)
            elif i in by_id and i not in seen:
                seen.add(i)
                out += observations(by_id[i].evidence_ids, seen)
        return out

    for c in claims:
        c.provenance = index.provenance(list(dict.fromkeys(observations(c.evidence_ids, {c.id}))))
    return NormalizedSources(claims)
