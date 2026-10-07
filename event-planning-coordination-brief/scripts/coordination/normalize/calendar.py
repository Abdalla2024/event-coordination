"""Calendar constraints -> one claim per row, one role claim per constraint type, note facts."""

from __future__ import annotations

import re
from datetime import date, datetime

from .base import Claim, held_claims, table_usable, unavailable_claim

SID = "SRC-CALENDAR"
# Constraint types the stakeholder described for the calendar (STK-I1-L235) plus the rows the
# disclosed calendar uses. A role with no row becomes an unsupported claim, never a default.
ROLES = ("preferred_event_window", "fallback_event_window", "venue_hold", "keynote_availability",
         "decision_deadline", "accessibility_walkthrough", "rehearsal_window", "teardown_deadline")

# Note text -> structured fact. Unmatched note text is kept verbatim, never dropped.
NOTE_PATTERNS = (
    ("hold_expires", re.compile(r"Hold expires (\d{4}-\d{2}-\d{2})"), lambda m: m.group(1)),
    ("keynote_unavailable_on_fallback", re.compile(r"Keynote unavailable on fallback date", re.I), lambda m: True),
    ("requires_venue_confirmation_first", re.compile(r"Venue confirmation required first", re.I), lambda m: True),
    ("remote_backup_acceptable", re.compile(r"Remote backup acceptable", re.I), lambda m: True),
    ("all_vendors_clear_by", re.compile(r"All vendors clear by (\d{1,2}:\d{2})"), lambda m: m.group(1)),
    ("label", re.compile(r"^(Preferred event date|Fallback date|Plan and budget decision)$"), lambda m: m.group(1)),
)


def note_facts(notes: str | None) -> tuple[dict, list[str]]:
    facts, unparsed = {}, []
    for seg in [s.strip() for s in re.split(r";", notes or "") if s.strip()]:
        for key, rx, conv in NOTE_PATTERNS:
            m = rx.search(seg)
            if m:
                facts[key] = conv(m)
                break
        else:
            unparsed.append(seg)
    return facts, unparsed


def normalize(captured, clock: datetime) -> list[Claim]:
    ok, status = table_usable(captured, SID)
    if not ok:
        return [unavailable_claim(f"N-CAL-ROLE-{r}", "calendar-role", f"Calendar {r}", SID, status)
                for r in ROLES]
    parsed = captured[SID].parsed
    obs_by_key = {o["record_key"]: o["id"] for o in parsed.observations}
    claims, by_type = [], {}
    for rid, row in parsed.records.items():
        oid = obs_by_key[rid]
        facts, unparsed = note_facts(row.get("notes"))
        evidence_status = "retrieved"
        stale_reason = None
        if "hold_expires" in facts and date.fromisoformat(facts["hold_expires"]) < clock.date():
            evidence_status, stale_reason = "stale", f"hold expired {facts['hold_expires']} before the business clock"
        claims.append(Claim(
            f"N-CAL-{rid}", "calendar-constraint",
            f"{rid} {row['constraint_type']} ({row['priority']}) {row['start_at']} – {row['end_at']}, owner {row['owner']}",
            {k: row[k] for k in ("constraint_id", "constraint_type", "owner", "start_at", "end_at", "priority")},
            "supported", evidence_status, [oid], [SID], owner=row["owner"],
            rationale=stale_reason,
            fields={"notes": row.get("notes"), "note_facts": facts, "note_unparsed": unparsed,
                    "record_version": row["record_version"], "recognized_type": row["constraint_type"] in ROLES}))
        by_type.setdefault(row["constraint_type"], []).append(rid)
    held = held_claims(captured, SID, "N-CAL", "calendar-constraint")
    held_ids = {c.fields["record_key"] for c in held}
    claims += held
    for role in ROLES:
        rows = by_type.get(role, [])
        if len(rows) == 1:
            claims.append(Claim(f"N-CAL-ROLE-{role}", "calendar-role", f"Calendar {role} is {rows[0]}.",
                                rows[0], "supported", "retrieved", [obs_by_key[rows[0]]], [SID]))
        elif len(rows) > 1:
            claims.append(Claim(f"N-CAL-ROLE-{role}", "calendar-role",
                                f"Calendar {role} appears in several rows {rows}; none is chosen.",
                                None, "conflicting", "unverified", [obs_by_key[r] for r in rows], [SID],
                                fields={"candidates": rows}))
        else:
            why = "a held row may carry it" if held_ids else "no row has this type"
            claims.append(Claim(f"N-CAL-ROLE-{role}", "calendar-role", f"Calendar {role}: not found ({why}).",
                                None, "unsupported" if not held_ids else "unresolved",
                                "unverified" if held_ids else "retrieved", [SID], [SID]))
    return claims
