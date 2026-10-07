"""Event brief, official venue and floor-plan normalization; cross-checks and prerequisites."""

import json

from factories import BRIEF, PDF, normalized, notion
from coordination.normalize.brief import _list
from coordination.util import sha256_bytes


def brief_with(replace: dict = None, add: list = None):
    blocks = [(t, (replace or {}).get(i, x)) for i, (t, x) in enumerate(BRIEF)] + (add or [])
    return notion(blocks)


def test_brief_facts(tmp_path):
    n = normalized(tmp_path)
    v = lambda k: n.get(f"N-BRIEF-{k}").value
    assert v("planning_people") == 245 and v("planning_ceiling_twd") == 520000
    assert v("preferred_date") == "2026-10-17" and v("fallback_date_text") == "24 October"
    assert [i["key"] for i in v("hard_requirements")] == ["step_free_access", "wheelchair_seating", "live_captions",
                                                          "staffed_quiet_room", "opening_time", "completion_time"]
    assert v("quiet_space") == {"room": "V.I.P. Room", "occupancy": 20}
    assert v("wheelchair_spaces") == 6 and v("demo_count") == 3
    assert v("step_free_route_case")[2] == "V.I.P. Room"
    assert v("readiness_base_bundles") == {"catering_alternatives": ["Q-003", "Q-004"],
                                           "common": ["Q-005", "Q-006", "Q-009", "Q-010"]}
    assert v("required_outputs")[-1] == "unsent attendee and vendor messages"
    ceiling = n.get("N-BRIEF-planning_ceiling_twd")
    assert len(ceiling.fields["extraction"]) == 2        # both mentions found and agree
    assert n.get("N-BRIEF-audience_places").fields["case_record"] is True
    assert n.get("N-BRIEF-planning_people").fields["case_record"] is False


def test_brief_missing_fact_is_unsupported(tmp_path):
    n = normalized(tmp_path, SRC_BRIEF=brief_with({5: "Success is defined elsewhere."}))
    c = n.get("N-BRIEF-checkin_target_percent")
    assert c.support == "unsupported" and c.value is None


def test_brief_conflicting_ceiling(tmp_path):
    text = BRIEF[8][1].replace("TWD 520,000 ceiling", "TWD 480,000 ceiling")
    c = normalized(tmp_path, SRC_BRIEF=brief_with({8: text})).get("N-BRIEF-planning_ceiling_twd")
    assert c.support == "conflicting" and c.value is None and sorted(c.fields["candidates"]) == [480000, 520000]


def test_brief_uninterpretable_hard_requirement(tmp_path):
    text = BRIEF[4][1].replace("live captions,", "live captions, a helipad,")
    c = normalized(tmp_path, SRC_BRIEF=brief_with({4: text})).get("N-BRIEF-hard_requirements")
    assert c.support == "unresolved" and c.fields["detail"][0]["unmapped"] == ["a helipad"]


def test_brief_unavailable_withholds_every_fact(tmp_path):
    n = normalized(tmp_path, SRC_BRIEF=None)
    facts = n.of_kind("brief-fact")
    assert facts and all(c.support == "unsupported" for c in facts)
    assert n.get("X-headcount-brief-vs-signals").support == "unresolved"


def test_brief_invalid_page_data(tmp_path):
    bad = json.dumps({"cursor": {"stack": []}, "recordMap": {"block": {}}}).encode()
    n = normalized(tmp_path, SRC_BRIEF=bad)
    assert all(c.evidence_status == "invalid" for c in n.of_kind("brief-fact"))


def test_list_splitting():
    assert _list("a, b, and c d") == ["a", "b", "c d"]
    assert _list("a, b and c") == ["a", "b", "c"]
    assert _list("x, unsent attendee and vendor messages, and y") == ["x", "unsent attendee and vendor messages", "y"]


def test_cross_checks_consistent(tmp_path):
    n = normalized(tmp_path)
    for cid in ("X-preferred-date", "X-fallback-date", "X-event-window", "X-hard-requirement-times", "X-keynote",
                "X-venue-window", "X-teardown-window", "X-setup-window", "X-venue-amount", "X-business-clock",
                "X-demo-roster", "X-dietary-brief-vs-signals", "X-allowance-categories"):
        assert n.get(cid).support == "supported", (cid, n.get(cid).summary)


def test_cross_check_inconsistency_is_conflicting(tmp_path):
    text = BRIEF[12][1].replace("TWD 155,000 package", "TWD 150,000 package")
    x = normalized(tmp_path, SRC_BRIEF=brief_with({12: text})).get("X-venue-amount")
    assert x.support == "conflicting" and x.value is None and x.owner == "Operations"


def test_brief_reference_to_unknown_quote_is_held(tmp_path):
    text = BRIEF[14][1].replace("supplies staffing under Q-010", "supplies staffing under Q-099")
    x = normalized(tmp_path, SRC_BRIEF=brief_with({14: text})).get("X-brief-quote-Q-099")
    assert x.support == "unresolved"


def test_hall_facts_and_tariff_difference_keeps_case_value(tmp_path):
    n = normalized(tmp_path)
    assert n.get("N-VENUE-official_rate_weekend_twd_per_slot").value == 170000
    assert n.get("N-VENUE-official_rate_weekend_twd_per_slot").fields["replaces_case_amount"] is False
    t = n.get("X-venue-tariff-difference")
    assert t.value == {"planning_value_twd": 155000, "official_rate_twd_per_slot": 170000, "event_day_kind": "weekend"}
    assert t.fields["planning_value_replaced"] is False


def test_hall_unavailable(tmp_path):
    n = normalized(tmp_path, SRC_TICC_HALL=None)
    assert n.get("N-VENUE-official_rule_technical_and_safety_briefing").support == "unsupported"
    t = n.get("X-venue-tariff-difference")
    assert t.value["planning_value_twd"] == 155000 and t.value["official_rate_twd_per_slot"] is None
    assert t.evidence_status == "unverified"
    p = n.get("P-ticc-technical-safety-briefing")
    assert p.support == "supported" and "N-VENUE-official_rule_technical_and_safety_briefing" in p.fields["missing_basis"]


def test_access_index_must_list_disclosed_plan(tmp_path):
    n = normalized(tmp_path, SRC_TICC_ACCESS=b"<html>Accessible Facilities Floor Plan, nothing linked</html>")
    assert n.get("N-VENUE-official_4f_accessible_plan_listed").support == "unsupported"


def _bound_floorplan(tmp_path, observations):
    f = tmp_path / "fp.json"
    f.write_text(json.dumps({"pdf_sha256": sha256_bytes(PDF), "read_by": "test", "observations": observations}))
    return f


def test_floor_plan_bound_observations_supported_and_recorded_in_stage02(tmp_path):
    obs = [{"id": "FP-a", "confidence": "clear", "region": [0.1, 0.2, 0.3, 0.4], "summary": "Hall here."},
           {"id": "FP-b", "confidence": "ambiguous", "region": [0.5, 0.5, 0.6, 0.6], "summary": "Unclear mark."}]
    from factories import capture
    from coordination.config import load_config
    from coordination.normalize import normalize_sources
    captured = capture(tmp_path)
    n = normalize_sources(captured, load_config().business_clock, _bound_floorplan(tmp_path, obs))
    a, b = n.get("N-FP-FP-a"), n.get("N-FP-FP-b")
    assert a.support == "supported" and a.fields["spatial_only"] is True
    assert a.fields["locator"]["kind"] == "page-region" and "x 0.10–0.30" in a.fields["locator"]["value"]
    assert b.support == "unresolved" and b.value is None
    rec_obs = {o["id"]: o for o in captured["SRC-TICC-4F"].record["observations"]}
    assert rec_obs["OBS-SRC-TICC-4F-FP-a"]["evidence_file"].endswith(".pdf")
    assert a.provenance[0]["locator"]["kind"] == "page-region"


def test_ev13_accessible_elevator_observation_is_supported_and_narrow(tmp_path):
    from coordination.normalize.venue import load_floorplan_observations
    ref = load_floorplan_observations()
    assert ref["pdf_sha256"] == "sha256:8805ab527b7bb202a70534120ed4037dbde633301f1935e80bd04f12a7c70367"
    ev13 = next(o for o in ref["observations"] if o["id"] == "FP-accessible-elevator-ev13")
    assert ev13["confidence"] == "clear"
    assert "marks EV13" in ev13["summary"] and "EV14 shows the plain Elevator symbol" in ev13["summary"]
    assert all(o["confidence"] == "clear" for o in ref["observations"])
    # Bound to matching bytes, the real reference file yields a supported spatial claim with its region.
    f = tmp_path / "fp.json"
    f.write_text(json.dumps({**ref, "pdf_sha256": sha256_bytes(PDF)}))
    c = normalized(tmp_path, floorplan_file=f).get("N-FP-FP-accessible-elevator-ev13")
    assert c.support == "supported" and c.fields["spatial_only"] is True
    assert c.fields["locator"] == {"kind": "page-region",
                                   "value": "page 1, x 0.35–0.38, y 0.32–0.36 (fractions of page from top-left)"}
    assert "OBS-SRC-TICC-4F-FP-accessible-elevator-ev13" in c.evidence_ids


def test_floor_plan_hash_mismatch_holds_observations(tmp_path):
    n = normalized(tmp_path)   # the reference file is bound to the real PDF, not the synthetic one
    fp = n.of_kind("floor-plan-observation")
    assert fp and all(c.support == "unresolved" and c.evidence_status == "unverified" for c in fp)


def test_floor_plan_unavailable_withholds_spatial_claims(tmp_path):
    fp = normalized(tmp_path, SRC_TICC_4F=None).of_kind("floor-plan-observation")
    assert fp and all(c.support == "unsupported" and c.evidence_status == "unavailable" for c in fp)


def test_prerequisites_open_with_owners_and_no_invented_deadline(tmp_path):
    n = normalized(tmp_path)
    p = {c.id: c for c in n.of_kind("prerequisite")}
    assert set(p) == {"P-venue-confirmation", "P-accessibility-walkthrough", "P-ticc-technical-safety-briefing",
                      "P-severe-allergy-contacts", "P-livestream-network-test-Q-008",
                      "P-livestream-venue-confirmation-Q-008"}
    for c in p.values():
        assert c.fields["completion_state"] == "open" and c.fields["completion_evidence"] == []
        assert c.fields["deadline"] is None
    assert p["P-ticc-technical-safety-briefing"].owner == "Operations"
    assert p["P-accessibility-walkthrough"].owner == "Learner Experience"
    assert p["P-accessibility-walkthrough"].fields["depends_on"] == ["P-venue-confirmation"]
    assert p["P-venue-confirmation"].fields["applies_to"] == ["Q-001", "Q-002"]
    assert p["P-severe-allergy-contacts"].fields["quote_specific_requirement"] == ["Q-004"]
