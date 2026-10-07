"""Official TICC sources -> venue facts; floor-plan observations bound to the captured PDF hash.

Official pages describe the real venue. Their published tariff is documented beside the negotiated
case amount and never replaces it (STK-I3-L205). The floor plan is spatial evidence only (STK-I3-L193).
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import REFERENCES_DIR
from .base import Claim, unavailable_claim

HALL, ACCESS, PLAN = "SRC-TICC-HALL", "SRC-TICC-ACCESS", "SRC-TICC-4F"
HALL_FACTS = {  # observation suffix -> (claim key, kind)
    "fixed-seats": ("official_fixed_seats", "venue-fact"),
    "rate-slots": ("official_rate_time_slots", "venue-fact"),
    "rate-weekday": ("official_rate_weekday_twd_per_slot", "venue-fact"),
    "rate-weekend": ("official_rate_weekend_twd_per_slot", "venue-fact"),
    "rule-livestream": ("official_rule_livestream_contract_vendors_only", "venue-rule"),
    "rule-briefing": ("official_rule_technical_and_safety_briefing", "venue-rule"),
}


def _source_ok(captured, sid) -> tuple[bool, str]:
    c = captured.get(sid)
    status = c.record["retrieval_status"] if c else "unavailable"
    return status == "retrieved", status


def normalize(captured, observations_file: Path | None = None) -> list[Claim]:
    return _hall(captured) + _access(captured) + _floor_plan(captured, observations_file)


def _hall(captured) -> list[Claim]:
    ok, status = _source_ok(captured, HALL)
    if not ok:
        return [unavailable_claim(f"N-VENUE-{key}", kind, f"Official venue fact {key}", HALL, status)
                for key, kind in HALL_FACTS.values()]
    obs = {o["id"].removeprefix(f"OBS-{HALL}-"): o for o in captured[HALL].record["observations"]}
    claims = []
    for suffix, (key, kind) in HALL_FACTS.items():
        o = obs.get(suffix)
        if o is None:
            claims.append(Claim(f"N-VENUE-{key}", kind, f"Official venue fact {key}: not found on the page.",
                                None, "unsupported", "retrieved", [HALL], [HALL]))
            continue
        value = o.get("value", o.get("text"))
        fields = {"scope": "official real-venue source", "locator": o["locator"]}
        if suffix.startswith("rate-"):
            fields.update({"currency": "TWD", "unit": "per time slot",
                           "replaces_case_amount": False, "basis": "STK-I3-L205"})
        claims.append(Claim(f"N-VENUE-{key}", kind, o["summary"], value, "supported", "retrieved",
                            [o["id"]], [HALL], fields=fields))
    return claims


def _access(captured) -> list[Claim]:
    ok, status = _source_ok(captured, ACCESS)
    if not ok:
        return [unavailable_claim("N-VENUE-official_4f_accessible_plan_listed", "venue-fact",
                                  "Official listing of the 4F accessible-facilities plan", ACCESS, status)]
    obs = {o["id"]: o for o in captured[ACCESS].record["observations"]}
    o = obs.get(f"OBS-{ACCESS}-4f")
    if o is None:
        return [Claim("N-VENUE-official_4f_accessible_plan_listed", "venue-fact",
                      "The disclosed 4F floor plan is not listed on the official accessibility index.",
                      None, "unsupported", "retrieved",
                      [i["id"] for i in captured[ACCESS].record["parse_issues"]] or [ACCESS], [ACCESS])]
    return [Claim("N-VENUE-official_4f_accessible_plan_listed", "venue-fact", o["summary"], o["url"],
                  "supported", "retrieved", [o["id"]], [ACCESS])]


def load_floorplan_observations(path: Path | None = None) -> dict:
    return json.loads((path or REFERENCES_DIR / "floorplan-observations.json").read_text(encoding="utf-8"))


def _floor_plan(captured, observations_file: Path | None) -> list[Claim]:
    ref = load_floorplan_observations(observations_file)
    ok, status = _source_ok(captured, PLAN)
    claims = []
    if not ok:
        # Image evidence unavailable: withhold every dependent spatial claim (assignment rule).
        for o in ref["observations"]:
            claims.append(Claim(f"N-FP-{o['id']}", "floor-plan-observation",
                                f"Spatial observation {o['id']} withheld: floor plan is '{status}'.",
                                None, "unsupported", status if status != "retrieved" else "invalid",
                                [PLAN, "ASG-TRACE"], [PLAN], fields={"spatial_only": True}))
        return claims
    rec = captured[PLAN].record
    bound = rec["content_hash"] == ref["pdf_sha256"]
    existing = {x["id"] for x in rec["observations"]}
    for o in ref["observations"]:
        x0, y0, x1, y1 = o["region"]
        locator = {"kind": "page-region",
                   "value": f"page 1, x {x0:.2f}–{x1:.2f}, y {y0:.2f}–{y1:.2f} (fractions of page from top-left)"}
        oid = f"OBS-{PLAN}-{o['id']}"
        fields = {"spatial_only": True, "locator": locator, "confidence": o["confidence"],
                  "evidence_file": rec["local_reference"], "evidence_sha256": rec["content_hash"],
                  "observed_against_sha256": ref["pdf_sha256"], "read_by": ref["read_by"]}
        if bound and oid not in existing:
            # Stage 02 records the evidence path with each page/region locator (assignment rule).
            rec["observations"].append({"id": oid, "summary": o["summary"], "locator": locator,
                                        "confidence": o["confidence"], "evidence_file": rec["local_reference"],
                                        "read_by": ref["read_by"]})
        if not bound:
            claims.append(Claim(f"N-FP-{o['id']}", "floor-plan-observation",
                                f"{o['id']}: recorded against a different PDF version; held until the plan is read again.",
                                None, "unresolved", "unverified", [f"OBS-{PLAN}-document"], [PLAN],
                                fields={**fields, "candidate_summary": o["summary"]}))
        elif o["confidence"] != "clear":
            claims.append(Claim(f"N-FP-{o['id']}", "floor-plan-observation", f"{o['id']} (ambiguous): {o['summary']}",
                                None, "unresolved", "retrieved", [oid], [PLAN],
                                fields={**fields, "candidate_summary": o["summary"]}))
        else:
            claims.append(Claim(f"N-FP-{o['id']}", "floor-plan-observation", o["summary"], o["summary"],
                                "supported", "retrieved", [oid, "STK-I3-L193"], [PLAN], fields=fields))
    return claims
