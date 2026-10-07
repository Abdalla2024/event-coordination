"""Vendor quote normalization."""

from factories import VEN, VEN_H, normalized
from conftest import xlsx_bytes


def ven(rows, headers=VEN_H):
    return xlsx_bytes([headers] + rows, "Vendor Quotes")


def test_quotes_are_comparable_and_never_confirmed(tmp_path):
    n = normalized(tmp_path)
    q4 = n.get("N-QUOTE-Q-004")
    assert q4.value == {"quote_id": "Q-004", "vendor": "City Pantry", "category": "catering",
                        "package": "lunch and two breaks", "amount_twd": 126000, "capacity": 300,
                        "available_date": "2026-10-17", "valid_until": "2026-09-12", "status": "available"}
    for c in n.of_kind("vendor-quote"):
        assert c.fields["confirmed"] is False and c.fields["confirmation_evidence"] == []
        assert c.fields["booking_state"] in ("planning-state-not-confirmed", "condition-outstanding")
    assert n.get("N-QUOTE-Q-001").fields["booking_state"] == "planning-state-not-confirmed"
    assert "STK-I3-L25" in n.get("N-QUOTE-Q-001").evidence_ids
    assert n.get("N-QUOTE-Q-008").fields["booking_state"] == "condition-outstanding"


def test_features_prerequisites_and_facts(tmp_path):
    n = normalized(tmp_path)
    assert n.get("N-QUOTE-Q-006").fields["features"]["hearing_loop"]["value"] is True
    assert n.get("N-QUOTE-Q-007").fields["features"]["hearing_loop"]["value"] is False
    assert "livestream_network_test" in n.get("N-QUOTE-Q-008").fields["prerequisites"]
    assert "named_allergy_contacts" in n.get("N-QUOTE-Q-004").fields["prerequisites"]
    assert n.get("N-QUOTE-Q-009").fields["facts"]["staff_count"]["value"] == 4
    assert n.get("N-QUOTE-Q-005").fields["facts"]["captioner_count"]["value"] == 2
    assert n.get("N-QUOTE-Q-002").fields["facts"]["keynote_unavailable_on_date"]["value"] is True
    f = n.get("N-QUOTE-Q-006").fields["features"]["hearing_loop"]
    assert f["field"] == "option" and f["pattern"] == "hearing-loop-included"


def test_capacity_population_not_invented(tmp_path):
    c = normalized(tmp_path).get("N-QUOTE-Q-003")
    assert c.fields["capacity_population"] is None and "STK-I3-L133" in c.fields["capacity_population_note"]


def test_unrecognized_note_text_is_kept(tmp_path):
    rows = [r if r[0] != "Q-009" else r[:9] + ["Includes first aid lead; parking not included"] for r in VEN]
    c = normalized(tmp_path, SRC_VENDOR=ven(rows)).get("N-QUOTE-Q-009")
    assert c.fields["note_unparsed"] == ["parking not included"]


def test_option_and_note_disagreement_is_reported_not_merged(tmp_path):
    rows = [r if r[0] != "Q-006" else r[:9] + ["No hearing loop included"] for r in VEN]
    c = normalized(tmp_path, SRC_VENDOR=ven(rows)).get("N-QUOTE-Q-006")
    assert "hearing_loop" not in c.fields["features"]
    assert c.fields["text_conflicts"][0]["key"] == "hearing_loop"


def test_expired_quote_is_stale(tmp_path):
    rows = [r if r[0] != "Q-003" else r[:7] + ["2026-08-25"] + r[8:] for r in VEN]
    n = normalized(tmp_path, SRC_VENDOR=ven(rows))
    q = n.get("N-QUOTE-Q-003")
    assert q.support == "supported" and q.evidence_status == "stale" and q.fields["valid_at_business_clock"] is False
    v = n.get("X-quote-validity-Q-003")
    assert v.evidence_status == "stale" and v.value["valid_through_decision_deadline"] is False


def test_validity_against_decision_deadline(tmp_path):
    rows = [r if r[0] != "Q-005" else r[:7] + ["2026-09-01"] + r[8:] for r in VEN]
    v = normalized(tmp_path, SRC_VENDOR=ven(rows)).get("X-quote-validity-Q-005")
    assert v.value == {"valid_at_business_clock": True, "valid_through_decision_deadline": False}


def test_conflicting_quotes_for_same_package_and_date(tmp_path):
    dup = ["Q-011", "Green Table", "catering", "lunch and two breaks", 99000, 260, "2026-10-17", "2026-09-07",
           "available", ""]
    n = normalized(tmp_path, SRC_VENDOR=ven(VEN + [dup]))
    conflict = n.get("N-QUOTE-CONFLICT-Q-003-Q-011")
    assert conflict.support == "conflicting" and conflict.value is None
    assert n.get("N-QUOTE-Q-003").fields["conflicts_with"] == ["Q-011"]


def test_duplicate_quote_id_held(tmp_path):
    n = normalized(tmp_path, SRC_VENDOR=ven(VEN + [VEN[2][:4] + [1] + VEN[2][5:]]))
    c = n.get("N-QUOTE-Q-003")
    assert c.support == "conflicting" and "duplicate-id" in c.fields["issue_kinds"]


def test_unknown_status_held(tmp_path):
    rows = [r if r[0] != "Q-010" else r[:8] + ["booked"] + r[9:] for r in VEN]
    c = normalized(tmp_path, SRC_VENDOR=ven(rows)).get("N-QUOTE-Q-010")
    assert c.support == "unresolved" and c.value is None


def test_reordered_columns_same_quotes(tmp_path):
    order = list(reversed(range(len(VEN_H))))
    a = normalized(tmp_path / "a")
    b = normalized(tmp_path / "b", SRC_VENDOR=ven([[r[i] for i in order] for r in VEN], [VEN_H[i] for i in order]))
    assert [c.value for c in a.of_kind("vendor-quote")] == [c.value for c in b.of_kind("vendor-quote")]


def test_vendor_unavailable(tmp_path):
    n = normalized(tmp_path, SRC_VENDOR=None)
    assert n.get("N-QUOTE-source").support == "unsupported"
    assert n.get("X-venue-amount").support == "unresolved"
    assert n.get("X-venue-tariff-difference").support == "unresolved"
