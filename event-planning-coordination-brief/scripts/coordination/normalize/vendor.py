"""Vendor quotes -> comparable quote records with booking state, validity, features and prerequisites.

Held and available are planning states, never confirmations (STK-I2-L113, STK-I3-L25); no quote is
marked confirmed because no disclosed source records a confirmation. Note text is matched against
explicit patterns; anything unmatched is kept verbatim as unparsed, never interpreted by guess.
"""

from __future__ import annotations

import re
from datetime import datetime

from ..policy import quote_valid_at
from .base import Claim, held_claims, table_usable, to_int, unavailable_claim

SID = "SRC-VENDOR"
BOOKING_STATE = {
    "held": ("planning-state-not-confirmed", ["STK-I2-L113", "STK-I3-L25"]),
    "available": ("planning-state-not-confirmed", ["STK-I2-L101", "STK-I3-L25"]),
    "conditional": ("condition-outstanding", ["STK-I2-L101"]),
}

# (pattern id, regex, kind, key, value-from-match). kind: feature | prerequisite | fact
PATTERNS = (
    ("hearing-loop-included", r"\bwith hearing loop\b", "feature", "hearing_loop", lambda m: True),
    ("hearing-loop-excluded", r"\bNo hearing loop included\b", "feature", "hearing_loop", lambda m: False),
    ("live-captions", r"\blive captions\b", "feature", "live_captions", lambda m: True),
    ("transcript", r"\btranscript\b", "feature", "transcript", lambda m: True),
    ("captioners", r"\b(\w+) captioners included\b", "fact", "captioner_count", lambda m: to_int(m.group(1))),
    ("quiet-room-staffing", r"\bquiet room staffing\b", "feature", "quiet_room_staffing", lambda m: True),
    ("livestream", r"\blivestream\b", "feature", "livestream", lambda m: True),
    ("av-package", r"\bAV package\b", "feature", "av_package", lambda m: True),
    ("meals", r"^lunch and two breaks$", "feature", "meal_service", lambda m: "lunch and two breaks"),
    ("dietary", r"Supports listed vegetarian and halal meals", "feature", "dietary_vegetarian_halal", lambda m: True),
    ("first-aid", r"Includes first aid lead", "feature", "first_aid_lead", lambda m: True),
    ("staff-count", r"^(\w+) staff$", "fact", "staff_count", lambda m: to_int(m.group(1))),
    ("venue-package", r"Plenary Hall .*allocation plus V\.I\.P\. Room", "feature", "venue_package",
     lambda m: m.group(0)),
    ("network-test", r"Network test required", "prerequisite", "livestream_network_test", lambda m: True),
    ("named-allergy-contacts", r"Allergy process requires named contacts", "prerequisite",
     "named_allergy_contacts", lambda m: True),
    ("room-from-venue", r"Room itself supplied by venue", "prerequisite", "room_supplied_by_venue", lambda m: True),
    ("setup-start", r"Setup starts at (\d{1,2}:\d{2})", "fact", "setup_starts_at", lambda m: m.group(1)),
    ("keynote-unavailable", r"Keynote is unavailable on this date", "fact", "keynote_unavailable_on_date",
     lambda m: True),
    ("ticc-coordination", r"supplied through TICC coordination in this synthetic case", "fact", "supply_route",
     lambda m: "TICC coordination (synthetic case)"),
    ("synthetic-full-day", r"Synthetic full-day package", "fact", "package_scope", lambda m: "full-day (synthetic)"),
    ("see-venue-note", r"see venue coordination note", "fact", "refers_to_venue_coordination_record",
     lambda m: True),
    ("no-real-reservation", r"no real reservation", "fact", "real_reservation", lambda m: False),
)
COMPILED = [(pid, re.compile(rx, re.I), kind, key, conv) for pid, rx, kind, key, conv in PATTERNS]


def extract(text: str, field_name: str) -> tuple[dict, list[str]]:
    """Return ({kind: {key: {value, pattern, text, field}}}, unparsed segments) for one text field."""
    found: dict = {"feature": {}, "prerequisite": {}, "fact": {}}
    unparsed = []
    for seg in [s.strip() for s in (text or "").split(";") if s.strip()]:
        matched = False
        for pid, rx, kind, key, conv in COMPILED:
            m = rx.search(seg)
            if m:
                found[kind][key] = {"value": conv(m), "pattern": pid, "text": seg, "field": field_name}
                matched = True
        if not matched and field_name == "notes":
            unparsed.append(seg)
    return found, unparsed


def normalize(captured, clock: datetime) -> list[Claim]:
    ok, status = table_usable(captured, SID)
    if not ok:
        return [unavailable_claim("N-QUOTE-source", "vendor-quote", "Vendor quotes", SID, status)]
    parsed = captured[SID].parsed
    obs = {o["record_key"]: o["id"] for o in parsed.observations}
    claims = []
    for qid, row in parsed.records.items():
        state, state_basis = BOOKING_STATE[row["status"]]
        opt, _ = extract(row["option"], "option")
        note, note_un = extract(row.get("notes"), "notes")
        merged, text_conflicts = {}, []
        for k in opt:
            merged[k] = {}
            for key in set(opt[k]) | set(note[k]):
                a, b = opt[k].get(key), note[k].get(key)
                if a and b and a["value"] != b["value"]:
                    text_conflicts.append({"key": key, "option": a, "notes": b})
                else:
                    merged[k][key] = a or b
        valid = quote_valid_at(row["valid_until"], clock)
        claims.append(Claim(
            f"N-QUOTE-{qid}", "vendor-quote",
            f"{qid} {row['vendor']} {row['category']} '{row['option']}': TWD {row['quote_amount_twd']}, "
            f"capacity {row['capacity']}, date {row['available_date']}, valid until {row['valid_until']}, "
            f"status {row['status']} ({state})",
            {"quote_id": qid, "vendor": row["vendor"], "category": row["category"], "package": row["option"],
             "amount_twd": row["quote_amount_twd"], "capacity": row["capacity"],
             "available_date": row["available_date"], "valid_until": row["valid_until"],
             "status": row["status"]},
            "supported", "retrieved" if valid else "stale",
            [obs[qid]] + state_basis, [SID],
            rationale=None if valid else f"Quote expired before the business clock ({row['valid_until']}).",
            fields={
                "currency": "TWD",
                "booking_state": state,
                "confirmed": False,
                "confirmation_evidence": [],
                "valid_at_business_clock": valid,
                "capacity_population": None,
                "capacity_population_note": "The register states a capacity number only; who it covers is not "
                                            "stated in the package details (STK-I3-L133).",
                "features": merged["feature"],
                "prerequisites": merged["prerequisite"],
                "facts": merged["fact"],
                "notes": row.get("notes"),
                "note_unparsed": note_un,
                "text_conflicts": text_conflicts,
            }))
    claims += held_claims(captured, SID, "N-QUOTE", "vendor-quote")
    claims += _conflicting_quotes(claims)
    return claims


def _conflicting_quotes(claims: list[Claim]) -> list[Claim]:
    """Same vendor, category, package and date with different terms: flag, never choose."""
    groups: dict = {}
    for c in claims:
        if c.kind == "vendor-quote" and c.support == "supported":
            v = c.value
            groups.setdefault((v["vendor"], v["category"], v["package"], v["available_date"]), []).append(c)
    out = []
    for (vendor, cat, pkg, day), items in groups.items():
        terms = {(c.value["amount_twd"], c.value["capacity"], c.value["status"], c.value["valid_until"])
                 for c in items}
        if len(items) > 1 and len(terms) > 1:
            ids = [c.value["quote_id"] for c in items]
            out.append(Claim(f"N-QUOTE-CONFLICT-{'-'.join(ids)}", "quote-conflict",
                             f"Quotes {ids} offer the same {cat} package from {vendor} on {day} with different "
                             "terms; neither is chosen.", None, "conflicting", "unverified",
                             [e for c in items for e in c.evidence_ids[:1]] + ["STK-I1-L167"], [SID],
                             owner="Operations", fields={"quote_ids": ids}))
            for c in items:
                c.fields["conflicts_with"] = [i for i in ids if i != c.value["quote_id"]]
    return out
