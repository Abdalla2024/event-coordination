"""Phase 5 rendering, packaging and validation."""

import copy
import csv
import io
import json
import re

import icalendar
import pytest

from factories import ATT, ATT_H, VEN, VEN_H, render_input, twelve_demo_brief
from conftest import xlsx_bytes
from coordination.config import SKILL_DIR
from coordination.render import ARTIFACTS, MANIFEST, render_all, validate
from coordination.render import calendar_ics, view as viewmod
from coordination.render.csv_out import COLUMNS, REQUIRED
from coordination.render.plan_md import SECTIONS
from coordination.util import sha256_bytes

A, B = "OPT-2026-10-17-Q-003", "OPT-2026-10-17-Q-004"


def rendered(tmp_path, **kw):
    ri = render_input(tmp_path / "in", SRC_BRIEF=kw.pop("SRC_BRIEF", twelve_demo_brief()), **kw)
    out = tmp_path / "out"
    manifest = render_all(ri, out)
    files = {n: (out / n).read_text(encoding="utf-8") for n in ARTIFACTS}
    return ri, manifest, files, out


def csv_rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def failed(manifest):
    return [c["id"] for c in manifest["validation_checks"] if c["outcome"] != "pass"]


# ---------- package ----------

def test_all_files_exist_hashes_match_and_validation_passes(tmp_path):
    _, m, files, out = rendered(tmp_path)
    assert set(ARTIFACTS) <= {p.name for p in out.iterdir()} and (out / MANIFEST).exists()
    for a in m["artifacts"]:
        assert a["sha256"] == sha256_bytes((out / a["path"]).read_bytes()) and a["validation_status"] == "valid"
    assert failed(m) == [] and m["all_valid"]
    assert m["recommendation_status"] == "deferred-to-operations" and m["recommendation"] is None
    assert m["run_status"]["status"] == "partial"


def test_deterministic(tmp_path):
    ri = render_input(tmp_path / "in", SRC_BRIEF=twelve_demo_brief())
    a, b = render_all(ri, tmp_path / "a"), render_all(ri, tmp_path / "b")
    for name in ARTIFACTS + (MANIFEST,):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes(), name
    assert a == b


def test_rendering_does_not_mutate_phase3_4(tmp_path):
    ri = render_input(tmp_path / "in", SRC_BRIEF=twelve_demo_brief())
    before = copy.deepcopy({k: getattr(ri, k) for k in ri.__dataclass_fields__})
    m = render_all(ri, tmp_path / "out")
    assert {k: getattr(ri, k) for k in ri.__dataclass_fields__} == before
    assert next(c for c in m["validation_checks"] if c["id"] == "V-no-mutation")["outcome"] == "pass"


def test_renderer_imports_are_isolated():
    forbidden = ("capture", "normalize", "decide", "recommend", "transport", "sources", "sheets", "brief", "ticc")
    for p in (SKILL_DIR / "scripts" / "coordination" / "render").glob("*.py"):
        imports = re.findall(r"^\s*(?:from|import)\s+([\w.]+)", p.read_text(), re.M)
        bad = [i for i in imports if any(i.lstrip(".").split(".")[-1] == f or f".{f}" in i for f in forbidden)]
        assert not bad, (p.name, bad)


def test_view_values_equal_the_model(tmp_path):
    ri = render_input(tmp_path / "in", SRC_BRIEF=twelve_demo_brief())
    v = viewmod.build(ri)
    for o, mo in zip(v["options"], ri.decision["options"]):
        assert (o["id"], o["feasibility"], o["costs"]) == (mo["id"], mo["feasibility"], mo["costs"])
    assert v["recommendation"]["status"] == ri.recommendation["status"]
    assert v["recommendation"]["option"] == ri.recommendation["recommendation"]


# ---------- CSV ----------

def test_csv_columns_rows_and_values(tmp_path):
    ri, _, files, _ = rendered(tmp_path)
    header = files["vendor-comparison.csv"].splitlines()[0].split(",")
    assert header == COLUMNS and header[:11] == REQUIRED
    rows = csv_rows(files["vendor-comparison.csv"])
    assert [r["option_id"] for r in rows] == [o["id"] for o in ri.decision["options"]]   # model order, not cost
    for r, o in zip(rows, ri.decision["options"]):
        assert r["feasibility"] == o["feasibility"]
        total = o["costs"]["total_with_allowances_twd"]
        assert r["cost_twd"] == ("" if total is None else str(total))
        assert r["approval_status"] == "pending" and r["recommendation_outcome"] == "deferred-to-operations"
        assert r["planning_people"] == "245" and r["currency"] == "TWD"
        for col in ("quote_ids", "availability_status", "evidence_ids", "tradeoffs", "unresolved", "quote_details"):
            json.loads(r[col])
    by = {r["option_id"]: r for r in rows}
    assert by[A]["cost_twd"] == "494000" and by[B]["cost_twd"] == "512000"
    assert "held (planning state, not confirmed)" in by[A]["availability_status"]
    assert all(d["confirmation"] == "not confirmed" for d in json.loads(by[A]["quote_details"]).values())
    fallback = by["OPT-2026-10-24-fallback"]
    assert fallback["cost_twd"] == "" and "cost not stated" in fallback["unresolved"]
    assert "Hearing loop" in by[f"{A}-sub-Q-007"]["feasibility_reason"]
    assert "cost: better than" in by[A]["tradeoffs"] and by[f"{A}-sub-Q-007"]["tradeoffs"] == "[]"
    assert by[A]["remaining_under_ceiling_twd"] == "26000"


# ---------- ICS ----------

def test_ics_parses_and_events_are_tentative_drafts(tmp_path):
    ri, _, files, _ = rendered(tmp_path)
    cal = icalendar.Calendar.from_ical(files["event-calendar.ics"])
    assert str(cal["VERSION"]) == "2.0" and str(cal["METHOD"]) == "PUBLISH"
    events = list(cal.walk("VEVENT"))
    blocks = [b for b in ri.programme["blocks"] if b["kind"] != "buffer"]
    assert len(events) == 1 + len(blocks) + 2                # window + run of show + walkthrough + rehearsal
    uids = [str(e["UID"]) for e in events]
    assert len(set(uids)) == len(uids)
    for e in events:
        assert str(e["STATUS"]) == "TENTATIVE" and str(e["TRANSP"]) == "TRANSPARENT"
        assert "ATTENDEE" not in e and "ORGANIZER" not in e and "DTSTAMP" in e
        assert str(e["DTSTART"].dt.tzinfo) in ("Asia/Taipei", "CST") or e["DTSTART"].params["TZID"] == "Asia/Taipei"
        assert e["DTSTART"].params["TZID"] == e["DTEND"].params["TZID"] == "Asia/Taipei"
        assert "NOT BOOKED OR CONFIRMED" in str(e["DESCRIPTION"])
    days = {e["DTSTART"].dt.date().isoformat() for e in events}
    assert days == {"2026-10-17", "2026-09-25", "2026-10-16"}   # no deadline, hold-expiry or 24 Oct events
    summaries = " ".join(str(e["SUMMARY"]) for e in events)
    assert "briefing" not in summaries.lower() and "deadline" not in summaries.lower()


def test_ics_uids_stable_across_runs(tmp_path):
    a = rendered(tmp_path / "a")[2]["event-calendar.ics"]
    b = rendered(tmp_path / "b")[2]["event-calendar.ics"]
    uid = lambda t: re.findall(r"^UID:(.*)$", t.replace("\r\n ", ""), re.M)  # noqa: E731
    assert uid(a) == uid(b)


# ---------- plan ----------

def test_plan_sections_banner_and_key_content(tmp_path):
    _, _, files, _ = rendered(tmp_path)
    plan = files["event-plan.md"]
    positions = [plan.find(s) for s in SECTIONS]
    assert -1 not in positions and positions == sorted(positions)
    assert "run status `partial`" in plan and "`deferred-to-operations`" in plan
    assert "No option is recommended" in plan and "Recommended for Operations review" not in plan
    assert "Feasible options: 0. Conditional options: 2" in plan
    assert "**planner decision**" in plan and "Unallocated Programme buffer: 114 minutes" in plan
    assert "TWD 155000" in plan and "TWD 170000 per time slot" in plan and "not replaced" in plan
    assert "The brief asks for 2 feasible options; 0 are feasible" in plan
    assert "UNRESOLVED REFERENCE" not in plan


# ---------- communications ----------

def test_comms_vendor_drafts_only_for_candidate_quotes(tmp_path):
    _, _, files, _ = rendered(tmp_path)
    comms = files["draft-communications.md"]
    vendor_quotes = re.findall(r"## M\d+ — Vendor .*?confirmation request for (Q-\d+)", comms)
    assert vendor_quotes == ["Q-001", "Q-003", "Q-004", "Q-005", "Q-006", "Q-009", "Q-010"]
    assert "Q-007" not in comms and "Q-008" not in comms
    assert comms.count("**UNSENT DRAFT**") == comms.count("\n## M")
    assert "Attendees: accessibility and dietary acknowledgement" in comms
    assert "not a booking, order, commitment or approval" in comms


# ---------- validators ----------

@pytest.mark.parametrize("bad", ["Q-001 is booked for the event.", "The venue has been confirmed.",
                                 "Operations approved the plan.", "The Q-003 bundle was selected."])
def test_wording_check_catches_affirmative_claims(bad):
    assert validate.affirmative_claims(f"Intro text. {bad} More text.")


@pytest.mark.parametrize("ok", ["Nothing has been booked, approved, committed or confirmed.",
                                "The venue is not yet confirmed.", "Send only after the venue is confirmed.",
                                "Readiness is confirmed only for 2026-10-17; no readiness evidence for 2026-10-24."])
def test_wording_check_allows_negated_or_conditional_statements(ok):
    assert validate.affirmative_claims(ok) == []


def test_unsupported_amount_and_contact_details_are_caught(tmp_path):
    ri, _, files, _ = rendered(tmp_path)
    v = viewmod.build(ri)
    from coordination.render.cite import Citations
    tampered = dict(files)
    tampered["event-plan.md"] += "\nExtra cost TWD 999,999. Contact jane.doe@example.com or +886 912 345 678.\n"
    checks = {c["id"]: c for c in validate.run(ri, v, tampered, {"event-plan.md": [], "draft-communications.md": []},
                                               Citations(ri).known)}
    assert checks["V-amounts"]["outcome"] == "fail" and checks["V-privacy"]["outcome"] == "fail"


def test_status_or_cost_drift_is_caught(tmp_path):
    ri, _, files, _ = rendered(tmp_path)
    v = viewmod.build(ri)
    from coordination.render.cite import Citations
    tampered = dict(files)
    tampered["vendor-comparison.csv"] = files["vendor-comparison.csv"].replace(f"{A},", f"{A},", 1).replace(
        ",494000,TWD,conditional,", ",494000,TWD,feasible,", 1)
    checks = {c["id"]: c for c in validate.run(ri, v, tampered, {"event-plan.md": [], "draft-communications.md": []},
                                               Citations(ri).known)}
    assert checks["V-csv-rows"]["outcome"] == "fail"


def test_private_contact_column_does_not_leak(tmp_path):
    rows = [r + ["Jane Doe, jane@example.com, +886 912 345 678"] for r in ATT]
    _, m, files, _ = rendered(tmp_path, SRC_ATTENDEE=xlsx_bytes([ATT_H + ["contact"]] + rows, "Attendee Signals"))
    assert all("Jane" not in t and "@example.com" not in t for t in files.values())
    assert failed(m) == []


# ---------- scenarios ----------

def test_blocked_run_renders_empty_calendar_and_explains(tmp_path):
    _, m, files, _ = rendered(tmp_path, SRC_CALENDAR=None)
    assert m["run_status"]["status"] == "blocked"
    cal = icalendar.Calendar.from_ical(files["event-calendar.ics"])
    assert list(cal.walk("VEVENT")) == []
    assert "run status `blocked`" in files["event-plan.md"] and "run of show could not be planned" in files["event-plan.md"]
    assert failed(m) == []


def test_no_viable_option_renders_without_vendor_drafts(tmp_path):
    rows = ATT + [["SIG-099", "late_form", "fellows", "registered_attendees", 150, "people", "2026-08-25", "high"]]
    _, m, files, _ = rendered(tmp_path, SRC_ATTENDEE=xlsx_bytes([ATT_H] + rows, "Attendee Signals"))
    assert m["recommendation_status"] == "no-viable-option"
    assert "Vendor" not in files["draft-communications.md"]
    assert list(icalendar.Calendar.from_ical(files["event-calendar.ics"]).walk("VEVENT")) == []
    assert "No option is recommended" in files["event-plan.md"] and failed(m) == []


def test_unavailable_source_is_partial_with_reason(tmp_path):
    _, m, files, _ = rendered(tmp_path, SRC_TICC_HALL=None)
    assert m["run_status"]["status"] == "partial"
    assert any("sources not retrieved" in r for r in m["run_status"]["reasons"])
    assert "sources not retrieved" in files["event-plan.md"] and failed(m) == []


def test_recommended_conditional_is_rendered_as_conditional(tmp_path):
    rows = [r if r[0] != "Q-004" else r[:5] + [260] + r[6:] for r in VEN]
    _, m, files, _ = rendered(tmp_path, SRC_VENDOR=xlsx_bytes([VEN_H] + rows, "Vendor Quotes"))
    assert m["recommendation_status"] == "recommended-conditional" and m["recommendation"] == A
    assert f"Recommended for Operations review, conditionally: `{A}`." in files["event-plan.md"]
    assert m["run_status"]["status"] == "complete" and failed(m) == []


def test_ics_events_match_model_times(tmp_path):
    ri, _, files, _ = rendered(tmp_path)
    expected = calendar_ics.events(viewmod.build(ri))
    cal = icalendar.Calendar.from_ical(files["event-calendar.ics"])
    got = [(e["DTSTART"].dt.isoformat(), e["DTEND"].dt.isoformat()) for e in cal.walk("VEVENT")]
    assert [(x["start"], x["end"]) for x in expected] == [(s[:19] + "+08:00" if "+" not in s[19:] else s, e[:19] + "+08:00"
                                                            if "+" not in e[19:] else e) for s, e in got]
