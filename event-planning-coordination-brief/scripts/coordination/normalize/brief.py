"""Event brief prose -> named claims, each extracted by an explicit pattern with its matched text.

A fact found once (or repeated with the same value) is supported. Different values for the same
fact are conflicting and no value is chosen. A fact whose pattern no longer matches is unsupported:
later stages treat it as missing, never as a default. The venue coordination, readiness and
programme records are fictional case records (the brief says so); claims from them carry that scope.
"""

from __future__ import annotations

import json
import re

from .base import Claim, day_month_year, norm_space, to_int, unavailable_claim

SID = "SRC-BRIEF"
Q = r"Q-\d{3}"
# Sentence end: a full stop followed by space or end, but not the inner stops of "V.I.P."-style abbreviations.
END = r"(?<!\b[A-Z]\.[A-Z])\.(?=\s|$)"


def _list(text: str) -> list[str]:
    """Split an English list: 'a, b, and c' / 'a, b and c' -> ['a', 'b', 'c'].

    With an Oxford comma the final ', and' is the only conjunction split, so items such as
    'attendee and vendor messages' stay whole.
    """
    text = norm_space(text)
    if re.search(r",\s+(?:and|or)\s+", text):
        parts = re.split(r",\s*(?:and\s+|or\s+)?", text)
    else:
        parts = re.split(r",\s*|\s+(?:and|or)\s+(?=[^,]*$)", text)
    return [p.strip() for p in parts if p.strip()]


def _quotes(text: str) -> list[str]:
    return re.findall(Q, text)


HARD_REQUIREMENT_KEYS = (
    (r"^step-free access", "step_free_access"),
    (r"^wheelchair seating$", "wheelchair_seating"),
    (r"^live captions$", "live_captions"),
    (r"^a staffed quiet room$", "staffed_quiet_room"),
    (r"^a (\d{1,2}:\d{2}) opening$", "opening_time"),
    (r"^completion by (\d{1,2}:\d{2})$", "completion_time"),
)


def _hard_requirements(m):
    items, unmapped = [], []
    for raw in _list(m.group(1)):
        for rx, key in HARD_REQUIREMENT_KEYS:
            mm = re.match(rx, raw)
            if mm:
                items.append({"key": key, "text": raw, **({"time": mm.group(1)} if mm.groups() else {})})
                break
        else:
            unmapped.append(raw)
    if unmapped:
        return None, {"items": items, "unmapped": unmapped}
    return items, None


def _two_dates(m):
    first, second = m.group(1), m.group(2)
    year = re.search(r"\d{4}$", second)
    second_iso = day_month_year(second)
    first_iso = day_month_year(first) or (day_month_year(f"{first} {year.group(0)}") if year else None)
    if not (first_iso and second_iso):
        return None, {"text": m.group(0)}
    return {"dates": [first_iso, second_iso], "start": m.group(3), "end": m.group(4),
            "year_basis": "the phrase states the year once for both dates"}, None


# key -> (regex, converter returning value or (value, unresolved_detail), section filter, owner)
SPECS = {
    "event_name": (r"Plan the (.+?) at (.+?)" + END, lambda m: m.group(1), None),
    "venue_name": (r"Plan the (.+?) at (.+?)" + END, lambda m: m.group(2), None),
    "preferred_date": (r"preferred date is \w+ (\d{1,2} \w+ \d{4})", lambda m: day_month_year(m.group(1)), None),
    "fallback_date_text": (r"with \w+ (\d{1,2} \w+(?: \d{4})?) as a fallback", lambda m: m.group(1), None),
    "planning_people": (r"Plan for ([\d,]+) people", lambda m: to_int(m.group(1)), None),
    "planning_people_scope": (r"Plan for [\d,]+ people including ([^.]+)\.", lambda m: _list(m.group(1)), None),
    "required_outputs": (r"The draft must include (.+?)" + END, lambda m: _list(m.group(1)), None),
    "requested_feasible_options": (r"must include (\w+) feasible options", lambda m: to_int(m.group(1)), None),
    "hard_requirements": (r"Hard requirements are (.+?)" + END, _hard_requirements, None),
    "planning_ceiling_twd": (r"(?:planning ceiling is TWD ?([\d,]+)|TWD ([\d,]+) ceiling)",
                             lambda m: to_int(m.group(1) or m.group(2)), None),
    "no_expired_quote_or_unconfirmed_availability": (
        r"must not assume an expired quote or unconfirmed availability", lambda m: True, None),
    "checkin_target_percent": (r"at least (\d+) percent of registered attendees check in",
                               lambda m: to_int(m.group(1)), None),
    "success_all_demos_run": (r"all scheduled fellow demos run", lambda m: True, None),
    "success_accessibility_response_before_event": (
        r"accessibility requests receive a documented response before the event", lambda m: True, None),
    "plan_approver": (r"(\w+) approves the plan", lambda m: m.group(1), None),
    "spending_approver": (r"(Budget owners) approve spending", lambda m: m.group(1).lower(), None),
    "prohibited_automatic_actions": (r"Do not (.+?) automatically", lambda m: _list(m.group(1)), None),
    "business_clock_date": (r"simulated business clock (?:remains )?(\d{1,2} \w+ \d{4})",
                            lambda m: day_month_year(m.group(1)), None),
    "conditional_not_feasible_rule": (r"an option with a remaining hard-constraint dependency is conditional, not feasible",
                                      lambda m: True, None),
    "no_fabricated_second_option": (r"do not fabricate a second feasible option", lambda m: True, None),
    # Venue coordination record (fictional case record)
    "venue_record_id": (r"Record: (VEN-[\w-]+?);", lambda m: m.group(1), "Venue coordination record"),
    "venue_record_scope_note": (r"It is not (a statement from TICC, a real quote, accessibility certification, "
                                r"reservation or permission to use an outside supplier)",
                                lambda m: _list(m.group(1)), "Venue coordination record"),
    "venue_coverage": (r"covers (\d{1,2} \w+) and (\d{1,2} \w+ \d{4}), (\d{1,2}:\d{2})–(\d{1,2}:\d{2})",
                       _two_dates, "Venue coordination record"),
    "venue_package_amount_twd": (r"quoted TWD ([\d,]+) package", lambda m: to_int(m.group(1)),
                                 "Venue coordination record"),
    "venue_amount_is_negotiated_not_tariff": (r"synthetic negotiated all-inclusive venue amount, not an official "
                                              r"published tariff", lambda m: True, "Venue coordination record"),
    "audience_places": (r"allocates (\d+) usable audience places", lambda m: to_int(m.group(1)),
                        "Venue coordination record"),
    "audience_room": (r"usable audience places in the (.+?), including", lambda m: m.group(1),
                      "Venue coordination record"),
    "wheelchair_spaces": (r"including (\w+) wheelchair spaces", lambda m: to_int(m.group(1)),
                          "Venue coordination record"),
    "companions_use_ordinary_places": (r"companions use ordinary places", lambda m: True,
                                       "Venue coordination record"),
    "quiet_space": (r"\bThe ([^;]{1,40}?) on the same floor is the quiet space, with occupancy up to (\d+) people",
                    lambda m: {"room": m.group(1), "occupancy": to_int(m.group(2))}, "Venue coordination record"),
    "excluded_room": (r"(Room \d+) is not selected: (.+?)" + END,
                      lambda m: {"room": m.group(1), "reason": m.group(2)}, "Venue coordination record"),
    "step_free_route_case": (r"venue coordination confirms step-free access between (.+?)" + END,
                             lambda m: _list(m.group(1)), "Venue coordination record"),
    "floor_plan_does_not_prove": (r"it does not prove (.+?)" + END, lambda m: _list(m.group(1)),
                                  "Venue coordination record"),
    # Kept as the sentence's own wording: without an Oxford comma its final 'and' is ambiguous.
    "venue_package_includes": (r"The package includes (.+?)" + END, lambda m: norm_space(m.group(1)),
                               "Venue coordination record"),
    "service_assignments": (r"(\w+) supplies (\w+) under (Q-\d{3})",
                            lambda m: {"vendor": m.group(1), "service": m.group(2), "quote_id": m.group(3)},
                            "Venue coordination record"),
    "external_supply_not_permitted_basis": (
        r"(Q-\d{3}/Q-\d{3}) catering and (Q-\d{3}/Q-\d{3}) AV are fictional TICC-coordinated service offers, "
        r"not permission to bring external food or equipment",
        lambda m: {"catering": _quotes(m.group(1)), "av": _quotes(m.group(2))}, "Venue coordination record"),
    "livestream_conditions": (r"StreamNorth (Q-\d{3}) still requires its stated (network test) and "
                              r"(venue confirmation) before use",
                              lambda m: {"quote_id": m.group(1), "conditions": [m.group(2), m.group(3)]},
                              "Venue coordination record"),
    "base_plan_service_confirmation": (
        r"confirms adequate (.+?) for the base plan using ((?:Q-\d{3}/?)+)",
        lambda m: {"services": _list(m.group(1)), "quote_ids": _quotes(m.group(2))}, "Venue coordination record"),
    "dietary_response_counts": (
        r"for the (\d+) vegetarian meals, (\d+) halal meals and (\w+) severe-allergy requests",
        lambda m: {"vegetarian_meal": to_int(m.group(1)), "halal_meal": to_int(m.group(2)),
                   "severe_allergy_follow_up": to_int(m.group(3))}, "Venue coordination record"),
    "dietary_response_covers_both_catering_options": (
        r"both catering options include an Operations-coordinated dietary response", lambda m: True,
        "Venue coordination record"),
    "named_contacts_holder": (r"Named contacts are held by (\w+)", lambda m: m.group(1), "Venue coordination record"),
    "no_booking_or_spend_approved": (r"No booking or spend has been approved", lambda m: True,
                                     "Venue coordination record"),
    "operations_review_package": (r"Operations receives (.+?)" + END, lambda m: _list(m.group(1)),
                                  "Venue coordination record"),
    "budget_owner_review_package": (r"Budget owners receive (.+?)" + END, lambda m: _list(m.group(1)),
                                    "Venue coordination record"),
    "human_response_fields": (r"retain (actor, subject, plan revision, timestamp, outcome and reasons)",
                              lambda m: _list(m.group(1)), "Venue coordination record"),
    # Readiness confirmation (fictional case record)
    "readiness_record_id": (r"Coordination clarification: (VEN-[\w-]+?);", lambda m: m.group(1), None),
    "readiness_date": (r"For the (\d{1,2} \w+ \d{4}) exercise plan", lambda m: day_month_year(m.group(1)), None),
    "readiness_base_bundles": (
        r"using either (Q-\d{3}) or (Q-\d{3}) together with ((?:Q-\d{3}, )*Q-\d{3} and Q-\d{3})",
        lambda m: {"catering_alternatives": [m.group(1), m.group(2)], "common": _quotes(m.group(3))}, None),
    "readiness_setup_window": (r"between (\d{1,2}:\d{2}) and the (\d{1,2}:\d{2}) opening",
                               lambda m: {"start": m.group(1), "end": m.group(2)}, None),
    "readiness_teardown_window": (r"between the (\d{1,2}:\d{2}) programme finish and (\d{1,2}:\d{2})",
                                  lambda m: {"start": m.group(1), "end": m.group(2)}, None),
    "readiness_scope_limit": (r"This confirms schedule feasibility for the exercise only, not (.+?);",
                              lambda m: _list(m.group(1)), None),
    "readiness_unresolved_quote_conditions": (r"(Q-\d{3})'s network-test and venue-confirmation conditions remain "
                                              r"unresolved", lambda m: m.group(1), None),
    "no_vendor_durations_or_buffer": (r"No individual vendor duration or additional mandatory buffer is specified",
                                      lambda m: True, None),
    "budget_allowance_categories": (r"(\w+) and (\w+) are budget allowances",
                                    lambda m: [m.group(1), m.group(2)], None),
    "security_quote": (r"(Q-\d{3}) is (\w+) security and first-aid staffing",
                       lambda m: {"quote_id": m.group(1), "vendor": m.group(2)}, None),
    # Programme confirmation (fictional case record)
    "programme_record_id": (r"Programme clarification: (PROG-[\w-]+?);", lambda m: m.group(1), None),
    "demo_count": (r"scheduled (\w+) team demonstrations", lambda m: to_int(m.group(1)), None),
    "demo_roster": (r"team demonstrations for .+?: ((?:DEMO-\d+, )+DEMO-\d+ and DEMO-\d+)",
                    lambda m: re.findall(r"DEMO-\d+", m.group(1)), None),
    "demo_presentation_minutes": (r"(\d+) minutes of presentation", lambda m: to_int(m.group(1)), None),
    "demo_changeover_minutes": (r"separate (\d+)-minute changeover", lambda m: to_int(m.group(1)), None),
    "demo_include_each_once": (r"Include each demonstration once", lambda m: True, None),
    "demos_add_no_people": (r"they add no people to the declared attendance", lambda m: True, None),
    "programme_keynote_and_window": (
        r"Keep the existing (\d{1,2}:\d{2})–(\d{1,2}:\d{2}) keynote and (\d{1,2}:\d{2})–(\d{1,2}:\d{2}) event window",
        lambda m: {"keynote": [m.group(1), m.group(2)], "event_window": [m.group(3), m.group(4)]}, None),
    "roster_change_owner": (r"(\w+) owns roster or duration changes", lambda m: m.group(1), None),
    "planner_schedule_choices": (r"The planner chooses (the demonstration order, grouping and compatible meal and "
                                 r"break schedule)", lambda m: m.group(1), None),
}
MULTI = {"service_assignments"}          # facts that legitimately occur more than once with different values
CASE_RECORD_SECTIONS = ("Venue coordination record", "Exercise readiness", "Exercise programme")


def normalize(captured) -> list[Claim]:
    c = captured.get(SID)
    status = c.record["retrieval_status"] if c else "unavailable"
    if c is None or status != "retrieved" or c.parsed is None:
        return [unavailable_claim(f"N-BRIEF-{k}", "brief-fact", f"Brief fact {k}", SID, status) for k in SPECS]
    section_of = {b["block_id"]: b["section"] for b in c.parsed.blocks}
    texts = [(o["id"], o["text"], section_of.get(o["block_id"], "")) for o in c.parsed.observations]
    native = c.record["version_metadata"].get("native_version") or {}
    claims = []
    for key, (rx, conv, section) in SPECS.items():
        pattern = re.compile(rx)
        hits = []
        for oid, text, sec in texts:
            if section and not sec.startswith(section):
                continue
            for m in pattern.finditer(text):
                out = conv(m)
                value, detail = out if isinstance(out, tuple) else (out, None)
                hits.append({"observation_id": oid, "section": sec, "matched_text": m.group(0),
                             "value": value, "detail": detail})
        claims.append(_claim(key, hits, native))
    return claims


def _claim(key: str, hits: list[dict], native: dict) -> Claim:
    cid = f"N-BRIEF-{key}"
    if not hits:
        return Claim(cid, "brief-fact", f"Brief fact '{key}': pattern not found in the captured brief.",
                     None, "unsupported", "retrieved", [SID], [SID],
                     rationale="Treated as missing; later stages must not assume a value.")
    obs_ids = [h["observation_id"] for h in hits]
    extraction = [{k: h[k] for k in ("observation_id", "section", "matched_text")} for h in hits]
    case = any(h["section"].startswith(CASE_RECORD_SECTIONS) for h in hits)
    common = dict(fields={"extraction": extraction, "case_record": case, "brief_native_version": native})
    bad = [h for h in hits if h["value"] is None]
    if bad:
        return Claim(cid, "brief-fact", f"Brief fact '{key}': text found but could not be interpreted.",
                     None, "unresolved", "invalid", obs_ids, [SID],
                     **{"fields": {**common["fields"], "detail": [h["detail"] for h in bad]}})
    if key in MULTI:
        values = [h["value"] for h in hits]
        return Claim(cid, "brief-fact", f"Brief fact '{key}': {values}", values, "supported", "retrieved",
                     obs_ids, [SID], **common)
    distinct = {json.dumps(h["value"], sort_keys=True) for h in hits}
    if len(distinct) > 1:
        return Claim(cid, "brief-fact", f"Brief fact '{key}' has different values in the brief; none is chosen.",
                     None, "conflicting", "unverified", obs_ids, [SID],
                     **{"fields": {**common["fields"], "candidates": [h["value"] for h in hits]}})
    value = hits[0]["value"]
    return Claim(cid, "brief-fact", f"Brief fact '{key}': {value}", value, "supported", "retrieved",
                 obs_ids, [SID], **common)
