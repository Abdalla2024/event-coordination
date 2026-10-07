import json

from coordination.brief import parse_brief
from coordination.ticc import parse_access_index, parse_hall, pdf_metadata

PAGE = "00000000-0000-0000-0000-000000000001"


def test_brief_blocks_sections_and_versions(notion_fixture):
    p = parse_brief(json.dumps(notion_fixture).encode(), PAGE)
    assert p.title == "Synthetic Brief"
    assert [b["text"] for b in p.blocks][:3] == ["Event brief", "Brief version: TEST-BRIEF-1", "Plan for 99 people."]
    assert p.native_version["brief_version"] == "TEST-BRIEF-1"
    assert p.native_version["venue_record"] == "VEN-TEST-1"
    assert p.native_version["notion_page_version"] == 7
    obs = {o["id"]: o for o in p.observations}
    assert obs["OBS-SRC-BRIEF-B05"]["locator"]["value"].startswith("Venue coordination record ¶1")
    assert p.issues == []


def test_brief_missing_child_block_is_reported(notion_fixture):
    del notion_fixture["recordMap"]["block"]["b-p2"]
    p = parse_brief(json.dumps(notion_fixture).encode(), PAGE)
    assert [i["kind"] for i in p.issues] == ["missing-block"]


def test_hall_facts_with_locators(fixture_bytes):
    obs, issues = parse_hall(fixture_bytes("ticc-hall.html"))
    by = {o["id"].removeprefix("OBS-SRC-TICC-HALL-"): o for o in obs}
    assert issues == []
    assert by["rate-weekend"]["value"] == 120000 and by["rate-weekday"]["value"] == 100000
    assert by["fixed-seats"]["value"] == 3122
    assert by["rule-briefing"]["text"].startswith("10.")
    assert by["rate-weekend"]["locator"]["kind"] == "section"


def test_hall_missing_facts_become_issues():
    obs, issues = parse_hall(b"<html><title>t</title><body>nothing</body></html>")
    assert {i["id"] for i in issues} == {"ISS-SRC-TICC-HALL-rate-weekday", "ISS-SRC-TICC-HALL-rate-weekend",
                                         "ISS-SRC-TICC-HALL-rule-livestream", "ISS-SRC-TICC-HALL-rule-briefing"}


def test_access_index_confirms_disclosed_floor_plan(fixture_bytes):
    base = "https://example.test/wSite/lp?x=1"
    obs, issues = parse_access_index(fixture_bytes("ticc-access.html"), base,
                                     "https://example.test/wSite/public/Attachment/f-4f.pdf")
    assert issues == [] and len(obs[0]["entries"]) == 2
    assert "4F" in obs[1]["summary"]
    _, issues = parse_access_index(fixture_bytes("ticc-access.html"), base, "https://example.test/other.pdf")
    assert issues[0]["kind"] == "fact-not-found"


def test_pdf_metadata():
    raw = b"%PDF-1.4\n<< /Type /Page >> << /Type /Pages >> << /ModDate (D:20240315053857Z) >>"
    assert pdf_metadata(raw) == {"page_count": 1, "pdf_mod_date": "2024-03-15T05:38:57Z"}
