"""Properties every normalized bundle must keep, whatever the inputs."""

import re
from pathlib import Path

import pytest

from factories import normalized
from coordination.config import SKILL_DIR, load_requirements_evidence
from coordination.normalize.base import Claim

SCENARIOS = {"all-present": {}, "brief-missing": {"SRC_BRIEF": None}, "vendor-missing": {"SRC_VENDOR": None},
             "calendar-missing": {"SRC_CALENDAR": None}, "venue-missing": {"SRC_TICC_HALL": None, "SRC_TICC_4F": None},
             "attendee-missing": {"SRC_ATTENDEE": None}}


@pytest.mark.parametrize("name", SCENARIOS)
def test_every_evidence_id_resolves(tmp_path, name):
    from factories import capture
    from coordination.config import load_config
    from coordination.normalize import normalize_sources
    captured = capture(tmp_path, **SCENARIOS[name])
    n = normalize_sources(captured, load_config().business_clock)
    known = set(load_requirements_evidence())
    for rec in (c.record for c in captured.values()):
        known.add(rec["id"])
        known |= {o["id"] for o in rec["observations"]}
        known |= {i["id"] for i in rec["parse_issues"]}
        known |= {a["id"] for a in rec["attempts"]}
    known |= {c.id for c in n.claims}
    for c in n.claims:
        dangling = set(c.evidence_ids) - known
        assert not dangling, (c.id, dangling)


@pytest.mark.parametrize("name", SCENARIOS)
def test_only_supported_claims_carry_values(tmp_path, name):
    for c in normalized(tmp_path, **SCENARIOS[name]).claims:
        if c.support != "supported":
            assert c.value is None, c.id
        else:
            assert c.evidence_ids, c.id


def test_supported_source_claims_have_provenance(tmp_path):
    for c in normalized(tmp_path).claims:
        if c.support == "supported" and c.kind not in ("prerequisite",):
            assert c.provenance, c.id
            assert all("retrieved_at" in p and "locator" in p for p in c.provenance)


def test_claim_model_rejects_values_on_unsupported_claims():
    with pytest.raises(ValueError):
        Claim("x", "k", "s", 5, "conflicting", "unverified", ["e"])
    with pytest.raises(ValueError):
        Claim("x", "k", "s", 5, "supported", "retrieved", [])
    with pytest.raises(ValueError):
        Claim("x", "k", "s", None, "maybe")


def test_no_claim_says_confirmed_booked_or_approved(tmp_path):
    for c in normalized(tmp_path).claims:
        rec = c.as_record()
        assert rec.get("confirmed") in (None, False)
        assert not re.search(r"\b(is|was|been) (booked|confirmed|approved|paid)\b", rec["summary"], re.I), c.id


def test_normalization_layer_is_read_only():
    """No network, booking, payment, messaging or calendar-write capability in the normalize package."""
    src = "\n".join(p.read_text() for p in (SKILL_DIR / "scripts" / "coordination" / "normalize").glob("*.py"))
    imports = re.findall(r"^\s*(?:from|import)\s+([\w.]+)", src, re.M)
    forbidden = ("urllib", "requests", "smtplib", "http", "socket", "transport", "capture", "email")
    assert not [m for m in imports if any(m.lstrip(".").startswith(f) for f in forbidden)], imports


def test_claim_kinds_used_by_later_phases_exist():
    """Guard against silently renamed claim kinds used by later phases."""
    kinds = {"calendar-constraint", "calendar-role", "budget-category", "attendee-group", "attendee-need",
             "vendor-quote", "brief-fact", "venue-fact", "venue-rule", "floor-plan-observation", "cross-check",
             "quote-validity", "documented-difference", "prerequisite"}
    found = set()
    for p in Path(SKILL_DIR / "scripts" / "coordination" / "normalize").glob("*.py"):
        found |= set(re.findall(r'"((?:calendar|budget|attendee|vendor|brief|venue|floor-plan|cross|quote|documented|prerequisite)[a-z-]*)"',
                                p.read_text()))
    assert kinds <= found
