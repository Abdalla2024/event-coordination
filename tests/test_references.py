"""The reference files must trace back to the original transcripts and to each other."""

import re

from conftest import REPO
from coordination.config import REFERENCES_DIR, load_requirements_evidence, load_sources


def transcript_line(path: str, line: int) -> str:
    return (REPO / path).read_text(encoding="utf-8").splitlines()[line - 1]


def test_stakeholder_quotes_are_verbatim_on_cited_line():
    for rec in load_requirements_evidence().values():
        if rec["group"] != "stakeholder":
            continue
        assert rec["quote"] in transcript_line(rec["interview"], rec["line"]), rec["id"]
        m = re.fullmatch(r"STK-I(\d)-L(\d+)", rec["id"])
        assert m and int(m.group(2)) == rec["line"], rec["id"]


def test_every_source_was_disclosed_on_the_cited_line():
    for src in load_sources():
        d = src["disclosed_in"]
        assert f"({src['disclosed_url']})" in transcript_line(d["interview"], d["line"]), src["id"]


def test_source_meaning_evidence_resolves():
    known = load_requirements_evidence()
    for src in load_sources():
        for eid in src["meaning_evidence"]:
            assert eid in known, (src["id"], eid)


def test_decision_policy_cites_only_known_evidence():
    text = (REFERENCES_DIR / "decision-policy.md").read_text(encoding="utf-8")
    cited = set(re.findall(r"\b((?:STK|ASG)-[A-Z0-9-]+?)(?=[\],\s])", text))
    known = load_requirements_evidence()
    assert cited, "policy should cite evidence"
    assert cited <= set(known), sorted(cited - set(known))


def test_required_source_roles_present():
    roles = {s["source_role"] for s in load_sources()}
    assert {"event-brief", "calendar", "budget", "attendee-signals", "vendor-record",
            "venue-page", "floor-plan-or-image"} <= roles


def test_business_clock_is_assignment_clock(config):
    assert config.business_clock.isoformat() == "2026-08-26T12:00:00+08:00"
    assert config.schema_path.name == "snapshot.schema.json" and config.schema_path.exists()
