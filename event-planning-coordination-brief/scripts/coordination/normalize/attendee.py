"""Attendee signals -> population groups and overlapping needs (aggregate counts only).

Stakeholder rule: fellows, partners, staff, speakers and forecast walk-ins are separate groups;
accessibility (and dietary) requests overlap them and are never added (STK-I1-L41, STK-I1-L87).
This module does not sum the groups; the headcount basis is built in the planning baseline.
"""

from __future__ import annotations

from datetime import date, datetime

from .base import Claim, held_claims, table_usable, unavailable_claim

SID = "SRC-ATTENDEE"
GROUPS = ("fellows", "partners", "staff", "speakers", "walk_ins")          # STK-I1-L41
POPULATION_SIGNALS = {"registered_attendees": "registered", "required_on_site": "required",
                      "expected_attendees": "forecast"}
NEEDS = {  # signal -> (need, expected unit)
    "wheelchair_spaces": ("wheelchair_seating", "people"),
    "mobility_companions": ("mobility_companion", "people"),
    "live_caption_requests": ("live_captions", "people"),
    "hearing_loop_requests": ("hearing_loop", "people"),
    "quiet_room_requests": ("quiet_room", "people"),
    "vegetarian_meals": ("vegetarian_meal", "meals"),
    "halal_meals": ("halal_meal", "meals"),
    "severe_allergy_follow_up": ("severe_allergy_follow_up", "people"),
}


def normalize(captured, clock: datetime) -> list[Claim]:
    ok, status = table_usable(captured, SID)
    if not ok:
        return ([unavailable_claim(f"N-ATT-group-{g}", "attendee-group", f"Attendee group {g}", SID, status)
                 for g in GROUPS]
                + [unavailable_claim(f"N-ATT-need-{n}", "attendee-need", f"Attendee need {n}", SID, status)
                   for n, _ in NEEDS.values()])
    parsed = captured[SID].parsed
    obs = {o["record_key"]: o["id"] for o in parsed.observations}
    claims, groups, needs = [], {}, {}

    for rid, row in parsed.records.items():
        late = date.fromisoformat(row["observed_at"]) > clock.date()
        base = dict(evidence_ids=[obs[rid]], source_ids=[SID])
        common = {"signal_id": rid, "observed_at": row["observed_at"], "confidence": row["confidence"],
                  "origin": row["source"], "unit": row["unit"]}
        if row["signal"] in POPULATION_SIGNALS and row["segment"] != "all":
            groups.setdefault(row["segment"], []).append((rid, row, late, base, common))
        elif row["signal"] in NEEDS and row["segment"] == "all":
            needs.setdefault(NEEDS[row["signal"]][0], []).append((rid, row, late, base, common))
        else:
            claims.append(Claim(f"N-ATT-other-{rid}", "attendee-signal",
                                f"{rid}: signal '{row['signal']}' for segment '{row['segment']}' has no "
                                "stakeholder-defined meaning; not counted.", None, "unresolved", "retrieved",
                                fields={"raw": {k: row[k] for k in ("segment", "signal", "value", "unit")}},
                                **base))

    def emit(prefix, kind, key, rows, expected_unit, extra):
        if len(rows) > 1:
            return Claim(f"{prefix}-{key}", kind, f"{key}: {len(rows)} rows disagree or repeat; none is chosen.",
                         None, "conflicting", "unverified", [obs[r[0]] for r in rows], [SID],
                         fields={"candidates": [{"signal_id": r[0], "value": r[1]["value"]} for r in rows]})
        rid, row, late, base, common = rows[0]
        if row["unit"] != expected_unit:
            return Claim(f"{prefix}-{key}", kind, f"{key}: unit '{row['unit']}' is not '{expected_unit}'; held.",
                         None, "unresolved", "invalid", fields={**common, "raw_value": row["value"]}, **base)
        status = "unverified" if late else "retrieved"
        note = "observed after the business clock" if late else None
        return Claim(f"{prefix}-{key}", kind, f"{key}: {row['value']} {row['unit']} ({row['signal']}, "
                     f"confidence {row['confidence']}, observed {row['observed_at']})",
                     row["value"], "supported", status, rationale=note, fields={**common, **extra(row)}, **base)

    for g in GROUPS:
        if g in groups:
            claims.append(emit("N-ATT-group", "attendee-group", g, groups[g], "people",
                               lambda r: {"basis": POPULATION_SIGNALS[r["signal"]], "counts_as_people": True}))
        else:
            claims.append(Claim(f"N-ATT-group-{g}", "attendee-group", f"Attendee group {g}: no signal found.",
                                None, "unsupported", "retrieved", [SID], [SID]))
    for g in sorted(set(groups) - set(GROUPS)):
        claims.append(Claim(f"N-ATT-group-{g}", "attendee-group",
                            f"Segment '{g}' is not one of the stakeholder's groups {list(GROUPS)}; not counted.",
                            None, "unresolved", "retrieved", [obs[r[0]] for r in groups[g]], [SID]))
    for need, unit in NEEDS.values():
        if need in needs:
            claims.append(emit("N-ATT-need", "attendee-need", need, needs[need], unit,
                               lambda r: {"overlaps_population": True, "counts_as_people": False}))
        else:
            claims.append(Claim(f"N-ATT-need-{need}", "attendee-need", f"Need {need}: no signal found.",
                                None, "unsupported", "retrieved", [SID], [SID]))
    claims += held_claims(captured, SID, "N-ATT-row", "attendee-signal")
    return claims
