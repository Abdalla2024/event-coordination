"""Calendar, budget and attendee normalization."""

from factories import ATT, ATT_H, BUD, BUD_H, CAL, CAL_H, normalized
from conftest import xlsx_bytes


def cal(rows, headers=CAL_H):
    return xlsx_bytes([headers] + rows, "Calendar Constraints")


def att(rows):
    return xlsx_bytes([ATT_H] + rows, "Attendee Signals")


# ---------- calendar ----------

def test_calendar_rows_roles_and_note_facts(tmp_path):
    n = normalized(tmp_path)
    assert n.get("N-CAL-ROLE-decision_deadline").value == "CAL-005"
    hold = n.get("N-CAL-CAL-003")
    assert hold.fields["note_facts"] == {"hold_expires": "2026-09-05"}
    assert hold.value["priority"] == "hard" and hold.evidence_status == "retrieved"
    assert n.get("N-CAL-CAL-006").fields["note_facts"]["requires_venue_confirmation_first"] is True
    assert n.get("N-CAL-CAL-008").fields["note_facts"]["all_vendors_clear_by"] == "18:30"
    assert n.get("N-CAL-CAL-001").provenance[0]["locator"] == {"kind": "cell-range",
                                                               "value": "'Calendar Constraints'!A2:H2"}


def test_calendar_reordered_with_extra_column_normalizes_identically(tmp_path):
    order = [7, 3, 0, 5, 1, 6, 2, 4]
    rows = [[r[i] for i in order] + ["ignored"] for r in reversed(CAL)]
    a = normalized(tmp_path / "a")
    b = normalized(tmp_path / "b", SRC_CALENDAR=cal(rows, [CAL_H[i] for i in order] + ["extra"]))
    for cid in ("N-CAL-CAL-001", "N-CAL-CAL-005", "N-CAL-ROLE-venue_hold"):
        assert a.get(cid).value == b.get(cid).value


def test_calendar_two_deadlines_conflict_and_dependent_checks_unresolved(tmp_path):
    extra = ["CAL-009", "Operations", "decision_deadline", "2026-09-01T17:00:00+08:00",
             "2026-09-01T17:00:00+08:00", "hard", "", "cal-v1"]
    n = normalized(tmp_path, SRC_CALENDAR=cal(CAL + [extra]))
    role = n.get("N-CAL-ROLE-decision_deadline")
    assert role.support == "conflicting" and role.value is None and role.fields["candidates"] == ["CAL-005", "CAL-009"]
    v = n.get("X-quote-validity-Q-001")
    assert v.value["valid_through_decision_deadline"] is None


def test_calendar_missing_role_is_unsupported_not_defaulted(tmp_path):
    n = normalized(tmp_path, SRC_CALENDAR=cal([r for r in CAL if r[0] != "CAL-004"]))
    assert n.get("N-CAL-ROLE-keynote_availability").support == "unsupported"
    assert n.get("X-keynote").support == "unresolved"


def test_calendar_expired_hold_is_stale(tmp_path):
    rows = [r if r[0] != "CAL-003" else r[:6] + ["Hold expires 2026-08-20"] + r[7:] for r in CAL]
    n = normalized(tmp_path, SRC_CALENDAR=cal(rows))
    assert n.get("N-CAL-CAL-003").evidence_status == "stale"


def test_calendar_unrecognized_note_text_kept_verbatim(tmp_path):
    rows = [r if r[0] != "CAL-007" else r[:6] + ["Remote backup acceptable; bring spare cables"] + r[7:] for r in CAL]
    c = normalized(tmp_path, SRC_CALENDAR=cal(rows)).get("N-CAL-CAL-007")
    assert c.fields["note_facts"] == {"remote_backup_acceptable": True}
    assert c.fields["note_unparsed"] == ["bring spare cables"]


def test_calendar_invalid_row_held(tmp_path):
    rows = [r if r[0] != "CAL-005" else r[:3] + ["2026-09-04T17:00:00"] + r[4:] for r in CAL]
    n = normalized(tmp_path, SRC_CALENDAR=cal(rows))
    assert n.get("N-CAL-CAL-005").support == "unresolved"
    assert n.get("N-CAL-ROLE-decision_deadline").support == "unresolved"


def test_calendar_renamed_header_holds_everything(tmp_path):
    hdr = ["constraint_id", "owner", "type", "start_at", "end_at", "priority", "notes", "record_version"]
    n = normalized(tmp_path, SRC_CALENDAR=cal(CAL, hdr))
    roles = [c for c in n.of_kind("calendar-role")]
    assert roles and all(c.support == "unresolved" and c.evidence_status == "invalid" for c in roles)


def test_calendar_unavailable(tmp_path):
    n = normalized(tmp_path, SRC_CALENDAR=None)
    assert all(c.support == "unsupported" and c.evidence_status == "unavailable" for c in n.of_kind("calendar-role"))
    # The stakeholder still requires the walkthrough; only its schedule and owner are unknown.
    p = n.get("P-accessibility-walkthrough")
    assert p.support == "supported" and p.owner is None and p.fields["scheduled_window"] is None
    assert p.fields["missing_basis"] == ["N-CAL-ROLE-accessibility_walkthrough"]


# ---------- budget ----------

def test_budget_categories(tmp_path):
    c = normalized(tmp_path).get("N-BUD-catering")
    assert c.value == {"category": "catering", "planned_amount_twd": 115000, "approval_limit_twd": 135000,
                       "committed_amount_twd": 0, "owner": "Operations"}
    assert c.owner == "Operations" and c.fields["currency"] == "TWD"


def test_budget_invalid_and_duplicate_rows(tmp_path):
    rows = BUD + [["catering", 1, 2, 0, "Ops", "bud-v1"], ["security", "lots", 1, 0, "Ops", "bud-v1"]]
    n = normalized(tmp_path, SRC_BUDGET=xlsx_bytes([BUD_H] + rows, "Budget"))
    assert n.get("N-BUD-catering").support == "conflicting"
    assert n.get("N-BUD-security").support == "conflicting"   # same id also in an invalid row
    assert n.get("N-BUD-venue").support == "supported"


def test_budget_unavailable(tmp_path):
    n = normalized(tmp_path, SRC_BUDGET=None)
    assert n.get("N-BUD-source").support == "unsupported"
    assert n.get("X-allowance-categories") is None


# ---------- attendee ----------

def test_attendee_groups_and_needs_are_separate(tmp_path):
    n = normalized(tmp_path)
    groups = {c.id: c.value for c in n.of_kind("attendee-group")}
    assert groups == {"N-ATT-group-fellows": 148, "N-ATT-group-partners": 32, "N-ATT-group-staff": 18,
                      "N-ATT-group-speakers": 12, "N-ATT-group-walk_ins": 35}
    wheel = n.get("N-ATT-need-wheelchair_seating")
    assert wheel.value == 6 and wheel.fields["overlaps_population"] and not wheel.fields["counts_as_people"]
    assert n.get("N-ATT-group-walk_ins").fields["basis"] == "forecast"
    assert n.get("X-headcount-brief-vs-signals").value["consistent"] is True


def test_attendee_duplicate_group_conflicts_and_headcount_unresolved(tmp_path):
    rows = ATT + [["SIG-099", "late_form", "fellows", "registered_attendees", 150, "people", "2026-08-25", "high"]]
    n = normalized(tmp_path, SRC_ATTENDEE=att(rows))
    c = n.get("N-ATT-group-fellows")
    assert c.support == "conflicting" and c.value is None and len(c.fields["candidates"]) == 2
    assert n.get("X-headcount-brief-vs-signals").support == "unresolved"


def test_attendee_count_differing_from_brief_is_conflicting(tmp_path):
    rows = [r if r[0] != "SIG-005" else r[:4] + [50] + r[5:] for r in ATT]
    x = normalized(tmp_path, SRC_ATTENDEE=att(rows)).get("X-headcount-brief-vs-signals")
    assert x.support == "conflicting" and x.value is None and "260" in x.fields["detail"]


def test_attendee_unit_mismatch_unknown_signal_and_late_observation(tmp_path):
    rows = [r if r[0] != "SIG-003" else r[:5] + ["meals"] + r[6:] for r in ATT]
    rows = [r if r[0] != "SIG-002" else r[:6] + ["2026-09-01"] + r[7:] for r in rows]
    rows += [["SIG-050", "registration_form", "all", "parking_requests", 3, "people", "2026-08-24", "high"]]
    n = normalized(tmp_path, SRC_ATTENDEE=att(rows))
    assert n.get("N-ATT-group-staff").support == "unresolved"
    assert n.get("N-ATT-other-SIG-050").support == "unresolved"
    late = n.get("N-ATT-group-partners")
    assert late.support == "supported" and late.evidence_status == "unverified"


def test_attendee_missing_group_unsupported(tmp_path):
    n = normalized(tmp_path, SRC_ATTENDEE=att([r for r in ATT if r[0] != "SIG-004"]))
    assert n.get("N-ATT-group-speakers").support == "unsupported"
    assert n.get("X-headcount-brief-vs-signals").support == "unresolved"


def test_attendee_extra_private_column_is_not_carried(tmp_path):
    rows = [r + ["Jane Doe, +886-000"] for r in ATT]
    n = normalized(tmp_path, SRC_ATTENDEE=xlsx_bytes([ATT_H + ["contact"]] + rows, "Attendee Signals"))
    text = str([c.as_record() for c in n.claims])
    assert "Jane Doe" not in text and "+886" not in text
