"""Synthetic source builders for normalization tests.

The data imitates the disclosed sources' structure so every pattern and cross-check can be exercised.
It is test data only and is never read by the skill's run.
"""

import json

from conftest import FakeTransport, ok, xlsx_bytes
from coordination.config import load_config, load_sources
from coordination.normalize import normalize_sources
from coordination.sources import capture_all
from coordination.transport import HttpResponse

PAGE = "3ba0b700-541e-81d0-af55-dc1a8f49f5af"  # the registry's page id, so capture accepts the fixture

CAL_H = ["constraint_id", "owner", "constraint_type", "start_at", "end_at", "priority", "notes", "record_version"]
CAL = [
    ["CAL-001", "Operations", "preferred_event_window", "2026-10-17T09:30:00+08:00", "2026-10-17T17:00:00+08:00", "hard", "Preferred event date", "cal-v1"],
    ["CAL-002", "Operations", "fallback_event_window", "2026-10-24T09:30:00+08:00", "2026-10-24T17:00:00+08:00", "soft", "Fallback date", "cal-v1"],
    ["CAL-003", "TICC", "venue_hold", "2026-10-17T07:30:00+08:00", "2026-10-17T18:30:00+08:00", "hard", "Hold expires 2026-09-05", "cal-v1"],
    ["CAL-004", "Programme", "keynote_availability", "2026-10-17T10:00:00+08:00", "2026-10-17T11:00:00+08:00", "hard", "Keynote unavailable on fallback date", "cal-v1"],
    ["CAL-005", "Operations", "decision_deadline", "2026-09-04T17:00:00+08:00", "2026-09-04T17:00:00+08:00", "hard", "Plan and budget decision", "cal-v1"],
    ["CAL-006", "Learner Experience", "accessibility_walkthrough", "2026-09-25T14:00:00+08:00", "2026-09-25T16:00:00+08:00", "hard", "Venue confirmation required first", "cal-v1"],
    ["CAL-007", "Programme", "rehearsal_window", "2026-10-16T15:00:00+08:00", "2026-10-16T18:00:00+08:00", "soft", "Remote backup acceptable", "cal-v1"],
    ["CAL-008", "TICC", "teardown_deadline", "2026-10-17T17:00:00+08:00", "2026-10-17T18:30:00+08:00", "hard", "All vendors clear by 18:30", "cal-v1"],
]
BUD_H = ["category", "planned_amount_twd", "approval_limit_twd", "committed_amount_twd", "owner", "record_version"]
BUD = [["venue", 155000, 180000, 0, "Operations", "bud-v1"], ["catering", 115000, 135000, 0, "Operations", "bud-v1"],
       ["accessibility", 65000, 80000, 0, "Learner Experience", "bud-v1"], ["production", 85000, 100000, 0, "Programme", "bud-v1"],
       ["communications", 25000, 30000, 0, "Communications", "bud-v1"], ["security", 25000, 35000, 0, "Operations", "bud-v1"],
       ["contingency", 40000, 50000, 0, "Operations", "bud-v1"]]
ATT_H = ["signal_id", "source", "segment", "signal", "value", "unit", "observed_at", "confidence"]
ATT = [["SIG-001", "registration_form", "fellows", "registered_attendees", 148, "people", "2026-08-24", "high"],
       ["SIG-002", "partner_form", "partners", "registered_attendees", 32, "people", "2026-08-24", "high"],
       ["SIG-003", "operations_plan", "staff", "required_on_site", 18, "people", "2026-08-25", "high"],
       ["SIG-004", "programme_plan", "speakers", "required_on_site", 12, "people", "2026-08-25", "high"],
       ["SIG-005", "forecast", "walk_ins", "expected_attendees", 35, "people", "2026-08-26", "medium"],
       ["SIG-006", "registration_form", "all", "wheelchair_spaces", 6, "people", "2026-08-24", "high"],
       ["SIG-007", "registration_form", "all", "mobility_companions", 4, "people", "2026-08-24", "high"],
       ["SIG-008", "registration_form", "all", "live_caption_requests", 23, "people", "2026-08-24", "high"],
       ["SIG-009", "registration_form", "all", "hearing_loop_requests", 7, "people", "2026-08-24", "medium"],
       ["SIG-010", "registration_form", "all", "quiet_room_requests", 9, "people", "2026-08-24", "high"],
       ["SIG-011", "registration_form", "all", "vegetarian_meals", 28, "meals", "2026-08-24", "high"],
       ["SIG-012", "registration_form", "all", "halal_meals", 12, "meals", "2026-08-24", "high"],
       ["SIG-013", "registration_form", "all", "severe_allergy_follow_up", 4, "people", "2026-08-24", "high"]]
VEN_H = ["quote_id", "vendor", "category", "option", "quote_amount_twd", "capacity", "available_date", "valid_until", "status", "notes"]
PKG = "4F Plenary Hall front-500 allocation plus V.I.P. Room"
TICC = "supplied through TICC coordination in this synthetic case"
VEN = [["Q-001", "TICC", "venue", PKG, 155000, 500, "2026-10-17", "2026-09-05", "held", "Synthetic full-day package; see venue coordination note; no real reservation"],
       ["Q-002", "TICC", "venue", PKG, 155000, 500, "2026-10-24", "2026-09-05", "available", "Keynote is unavailable on this date; Synthetic full-day package; see venue coordination note; no real reservation"],
       ["Q-003", "Green Table", "catering", "lunch and two breaks", 108000, 260, "2026-10-17", "2026-09-07", "available", f"Supports listed vegetarian and halal meals; {TICC}"],
       ["Q-004", "City Pantry", "catering", "lunch and two breaks", 126000, 300, "2026-10-17", "2026-09-12", "available", f"Allergy process requires named contacts; {TICC}"],
       ["Q-005", "ClearText", "accessibility", "live captions and transcript", 42000, 500, "2026-10-17", "2026-09-10", "available", "Two captioners included"],
       ["Q-006", "SoundArc", "production", "AV package with hearing loop", 78000, 500, "2026-10-17", "2026-09-08", "available", f"Setup starts at 07:30; {TICC}"],
       ["Q-007", "LiteStage", "production", "basic AV package", 52000, 500, "2026-10-17", "2026-09-08", "available", f"No hearing loop included; {TICC}"],
       ["Q-008", "StreamNorth", "production", "livestream add-on", 55000, 1000, "2026-10-17", "2026-09-11", "conditional", f"Network test required; {TICC}"],
       ["Q-009", "SafeVenue", "security", "four staff", 28000, 500, "2026-10-17", "2026-09-15", "available", "Includes first aid lead"],
       ["Q-010", "QuietWorks", "accessibility", "quiet room staffing", 18000, 20, "2026-10-17", "2026-09-10", "available", "Room itself supplied by venue"]]

BRIEF = [
    ("header", "Event brief"),
    ("text", "Brief version: TEST-BRIEF-1"),
    ("text", "Plan the Synthetic Demo Day at Test Convention Center. The preferred date is Saturday 17 October 2026, with Saturday 24 October as a fallback. Plan for 245 people including attendees, speakers, and staff."),
    ("text", "The draft must include two feasible options, a run of show, and unsent attendee and vendor messages."),
    ("text", "Hard requirements are step-free access to the main programme and restrooms, wheelchair seating, live captions, a staffed quiet room, a 09:30 opening, and completion by 17:00. The total approved planning ceiling is TWD 520000. The recommendation must not assume an expired quote or unconfirmed availability."),
    ("text", "Success means at least 80 percent of registered attendees check in, all scheduled fellow demos run, and accessibility requests receive a documented response before the event."),
    ("text", "Operations approves the plan. Budget owners approve spending. Do not send invitations, book a venue, commit to a vendor, make payment, or write to a production calendar automatically."),
    ("sub_header", "Exercise source clarification"),
    ("text", "Use the simulated business clock 26 August 2026 when evaluating quotes. Recommend within supported evidence; an option with a remaining hard-constraint dependency is conditional, not feasible. Retain alternatives; do not fabricate a second feasible option if one is unavailable. All original hard requirements and the TWD 520,000 ceiling remain."),
    ("header", "Venue coordination record"),
    ("text", "Record: VEN-TEST-1; case clock: 26 August 2026, Asia/Taipei."),
    ("text", "This is a synthetic test document. It is not a statement from TICC, a real quote, accessibility certification, reservation or permission to use an outside supplier."),
    ("text", "Operations' exercise record covers 17 October and 24 October 2026, 07:30–18:30. The quoted TWD 155,000 package is a synthetic negotiated all-inclusive venue amount, not an official published tariff. It allocates 500 usable audience places in the 4F Plenary Hall, including six wheelchair spaces; companions use ordinary places. The V.I.P. Room on the same floor is the quiet space, with occupancy up to 20 people. Room 401 is not selected: the official venue description warns about sound interference."),
    ("text", "For this case, venue coordination confirms step-free access between the 4F accessible elevators, audience area, V.I.P. Room and accessible restroom. The public floor plan supplies spatial locators; it does not prove today's elevator operation, unobstructed route, seating configuration or acoustic performance."),
    ("text", "The package includes setup and teardown access, the quiet space and its separation from the programme. QuietWorks supplies staffing under Q-010; ClearText supplies captions under Q-005. Q-003/Q-004 catering and Q-006/Q-007 AV are fictional TICC-coordinated service offers, not permission to bring external food or equipment. StreamNorth Q-008 still requires its stated network test and venue confirmation before use. The exercise record confirms adequate captioning, hearing-loop and allergy coordination for the base plan using Q-004/Q-005/Q-006/Q-010; both catering options include an Operations-coordinated dietary response for the 28 vegetarian meals, 12 halal meals and four severe-allergy requests. Named contacts are held by Operations."),
    ("text", "No booking or spend has been approved. Operations receives the versioned plan, selected date/room and unresolved issues. Budget owners receive their category cost, remaining ceiling and cited quote validity. If a later actual response is provided, retain actor, subject, plan revision, timestamp, outcome and reasons."),
    ("sub_header", "Exercise readiness confirmation"),
    ("text", "Coordination clarification: VEN-TEST-1-R2; the simulated business clock remains 26 August 2026."),
    ("text", "The base service bundles using either Q-003 or Q-004 together with Q-005, Q-006, Q-009 and Q-010 can complete setup between 07:30 and the 09:30 opening. These can finish teardown between the 17:00 programme finish and 18:30. This confirms schedule feasibility for the exercise only, not a completed real-world test, booking or spending approval; Q-008's network-test and venue-confirmation conditions remain unresolved until evidenced."),
    ("text", "No individual vendor duration or additional mandatory buffer is specified. Q-009 is SafeVenue security and first-aid staffing; communications and contingency are budget allowances, not additional vendor services."),
    ("sub_header", "Exercise programme confirmation"),
    ("text", "Programme clarification: PROG-TEST-1; the simulated business clock remains 26 August 2026."),
    ("text", "Programme has scheduled three team demonstrations for 17 October 2026: DEMO-01, DEMO-02 and DEMO-03. Each demonstration needs 10 minutes of presentation plus a separate 3-minute changeover allowance. Include each demonstration once. These are team slots; they add no people to the declared attendance."),
    ("text", "Keep the existing 10:00–11:00 keynote and 09:30–17:00 event window. Programme owns roster or duration changes."),
]

HALL_HTML = ("<html><head><title>Synthetic venue page</title></head><body><p>大會堂 固定座位共3,122席</p>"
             "<dl><dt>劇院型人數</dt><dd>3122</dd><dt>每時段租金</dt><dd>08:30-12:30 / 13:30-17:30</dd>"
             "<dt>週一～週五</dt><dd>159000 元</dd><dt>週六～週日</dt><dd>170000 元</dd></dl>"
             "<p>9.直播規則。</p><p>10.技術協調會及安全逃生講習規則。</p></body></html>")
ACCESS_HTML = ('<html><body><h2>Accessible Facilities Floor Plan</h2>'
               '<a href="public/Attachment/f1710485827023.pdf">3TICC 4F Accessible Facilities Floor Plan</a></body></html>')
PDF = b"%PDF-1.4\n<< /Type /Page >>\n<< /ModDate (D:20240315053857Z) >>\n%%EOF"


def notion(blocks, page=PAGE):
    ids = [f"blk-{i:02d}" for i in range(len(blocks))]
    rm = {page: {"value": {"value": {"id": page, "type": "page", "version": 1, "last_edited_time": 1767225600000,
                                     "properties": {"title": [["Synthetic brief"]]}, "content": ids}}}}
    for bid, (btype, text) in zip(ids, blocks):
        rm[bid] = {"value": {"value": {"id": bid, "type": btype, "properties": {"title": [[text]]}}}}
    return json.dumps({"cursor": {"stack": []}, "recordMap": {"block": rm}}).encode()


def bodies(**overrides):
    """Default body per source id; pass SOURCE_ID=None to make it unavailable, or bytes to replace it."""
    b = {
        "SRC-BRIEF": notion(BRIEF),
        "SRC-CALENDAR": xlsx_bytes([CAL_H] + CAL, "Calendar Constraints"),
        "SRC-BUDGET": xlsx_bytes([BUD_H] + BUD, "Budget"),
        "SRC-ATTENDEE": xlsx_bytes([ATT_H] + ATT, "Attendee Signals"),
        "SRC-VENDOR": xlsx_bytes([VEN_H] + VEN, "Vendor Quotes"),
        "SRC-TICC-HALL": HALL_HTML.encode(),
        "SRC-TICC-ACCESS": ACCESS_HTML.encode(),
        "SRC-TICC-4F": PDF,
    }
    b.update({k.replace("_", "-"): v for k, v in overrides.items()})
    return b


def capture(tmp_path, **overrides):
    srcs = load_sources()
    b = bodies(**overrides)
    responses = {}
    for s in srcs:
        body = b[s["id"]]
        if body is not None:
            responses[s["retrieval"]["request_url"]] = [ok(body)]
    t = FakeTransport(responses)
    return capture_all(srcs, load_config().http_profiles, t, tmp_path)


def normalized(tmp_path, floorplan_file=None, **overrides):
    return normalize_sources(capture(tmp_path, **overrides), load_config().business_clock, floorplan_file)


def http_404():
    return HttpResponse(404, {}, b"", None)
