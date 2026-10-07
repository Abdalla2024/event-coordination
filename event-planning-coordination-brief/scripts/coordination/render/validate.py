"""Validation of the rendered deliverables against the model they were rendered from."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime

from . import calendar_ics, csv_out, plan_md
from ..programme import check as programme_check

CLAIM_WORDS = re.compile(r"\b(booked|confirmed|approved|selected|secured|reserved|committed)\b", re.I)
# A match is acceptable only when its sentence, before the word, negates or conditions it.
NEGATION = re.compile(r"\b(not|no|nothing|never|neither|nor|without|unless|until|pending|cannot|can't|isn't|"
                      r"aren't|hasn't|haven't|after|once|if|whether|before|un\w+)\b", re.I)
# Exact phrasings that describe the scope of a source record, not a booking or confirmation of the plan.
SCOPE_PHRASES = (
    re.compile(r"Readiness is confirmed only for \d{4}-\d{2}-\d{2}"),   # Phase 3 readiness check (case record scope)
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(\+\d{1,3}[\s-]?\d{2,4}[\s-]?\d{3,4}|\b\d{2,4}-\d{3,4}-\d{3,4}\b)")
TWD = re.compile(r"TWD ([\d,]+)")


def affirmative_claims(text: str) -> list[str]:
    """Sentences that state booking/confirmation/approval/selection affirmatively."""
    hits = []
    for m in CLAIM_WORDS.finditer(text):
        start = max(text.rfind(". ", 0, m.start()), text.rfind("\n", 0, m.start()), text.rfind("|", 0, m.start())) + 1
        if any(p.search(text[max(0, m.start() - 20):m.end() + 30]) for p in SCOPE_PHRASES):
            continue
        if not NEGATION.search(text[start:m.start()]):
            hits.append(text[start:m.end() + 40].strip())
    return hits


def _ints(node, acc: set):
    if isinstance(node, bool):
        return acc
    if isinstance(node, int):
        acc.add(node)
    elif isinstance(node, dict):
        for v in node.values():
            _ints(v, acc)
    elif isinstance(node, list):
        for v in node:
            _ints(v, acc)
    return acc


def _unfold(ics: str) -> list[str]:
    lines = []
    for raw in ics.split("\r\n"):
        if raw.startswith(" ") and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def run(ri, view, files: dict[str, str], cited: dict[str, list[str]], citations_known) -> list[dict]:
    checks = []

    def add(cid, artifact, ok, summary, details=None):
        checks.append({"id": cid, "summary": summary, "evidence_ids": [ri.recommendation["decision"]["id"]],
                       "owner": None, "rationale": None if ok else f"failed: {details}", "outcome": "pass" if ok else "fail",
                       "artifact": artifact, "details": details})

    model_options = {o["id"]: o for o in ri.decision["options"]}
    rec = ri.recommendation
    allowed = _ints([ri.decision, ri.recommendation, ri.claims, ri.programme], set())

    # CSV
    rows = list(csv.reader(io.StringIO(files["vendor-comparison.csv"])))
    header, body = rows[0], rows[1:]
    add("V-csv-columns", "vendor-comparison.csv", header == csv_out.COLUMNS and header[:11] == csv_out.REQUIRED,
        "CSV has the 11 required columns in order, then the documented extra columns", header)
    problems = []
    if [r[0] for r in body] != [o["id"] for o in ri.decision["options"]]:
        problems.append("rows do not match the model's options in model order")
    for r in body:
        row = dict(zip(header, r))
        o = model_options.get(row["option_id"])
        if o is None:
            problems.append(f"unknown option {row['option_id']}")
            continue
        total = o["costs"]["total_with_allowances_twd"]
        if row["feasibility"] != o["feasibility"]:
            problems.append(f"{o['id']} feasibility differs")
        if row["cost_twd"] != ("" if total is None else str(total)):
            problems.append(f"{o['id']} cost differs")
        if row["recommendation_outcome"] != rec["status"]:
            problems.append(f"{o['id']} recommendation outcome differs")
        for col in ("quote_ids", "availability_status", "evidence_ids", "tradeoffs", "unresolved", "quote_details",
                    "allowances_twd"):
            try:
                json.loads(row[col])
            except ValueError:
                problems.append(f"{o['id']} {col} is not JSON")
        for col in ("planning_people", "cost_twd", "vendor_total_twd", "remaining_under_ceiling_twd"):
            if row[col] and not re.fullmatch(r"-?\d+", row[col]):
                problems.append(f"{o['id']} {col} is not an integer")
        if row["approval_status"] != "pending":
            problems.append(f"{o['id']} approval status is '{row['approval_status']}'")
        unknown = [i for i in json.loads(row["evidence_ids"]) if not citations_known(i)]
        if unknown:
            problems.append(f"{o['id']} unresolved evidence {unknown}")
    add("V-csv-rows", "vendor-comparison.csv", not problems,
        "Every CSV row matches its Phase 3 option (status, cost, approvals) and the Phase 4 outcome", problems)

    # Plan
    plan = files["event-plan.md"]
    positions = [plan.find(s) for s in plan_md.SECTIONS]
    add("V-plan-sections", "event-plan.md", -1 not in positions and positions == sorted(positions),
        "Event plan contains every required section in order", [s for s, p in zip(plan_md.SECTIONS, positions) if p < 0])
    banner_ok = (f"run status `{ri.run_status['status']}`" in plan and f"`{rec['status']}`" in plan)
    add("V-plan-banner", "event-plan.md", banner_ok, "Plan banner states the run status and recommendation outcome")
    rec_ok = (rec["recommendation"] is None and "Recommended for Operations review" not in plan
              and all("Recommended for Operations review" not in t for t in files.values())) or \
             (rec["recommendation"] is not None and rec["recommendation"] in plan)
    add("V-recommendation-match", "event-plan.md", rec_ok, "Deliverables state exactly the Phase 4 recommendation")

    # ICS
    lines = _unfold(files["event-calendar.ics"])
    expected = calendar_ics.events(view)
    vevents, cur = [], None
    for ln in lines:
        if ln == "BEGIN:VEVENT":
            cur = {}
        elif ln == "END:VEVENT":
            vevents.append(cur)
            cur = None
        elif cur is not None:
            k, _, v = ln.partition(":")
            cur[k] = v
    problems = []
    for need in ("BEGIN:VCALENDAR", "VERSION:2.0", "METHOD:PUBLISH", "END:VCALENDAR"):
        if need not in lines:
            problems.append(f"missing {need}")
    if any(ln.startswith(("ATTENDEE", "ORGANIZER")) for ln in lines):
        problems.append("ATTENDEE or ORGANIZER present")
    uids = [e.get("UID") for e in vevents]
    if len(uids) != len(set(uids)) or None in uids:
        problems.append("UIDs missing or not unique")
    for e, x in zip(vevents, expected):
        for key in ("DTSTAMP", "DTSTART;TZID=Asia/Taipei", "DTEND;TZID=Asia/Taipei"):
            if key not in e:
                problems.append(f"{e.get('UID')} missing {key}")
        if e.get("STATUS") != "TENTATIVE" or e.get("TRANSP") != "TRANSPARENT":
            problems.append(f"{e.get('UID')} not tentative/transparent")
        if e.get("DTSTART;TZID=Asia/Taipei") != calendar_ics._local(x["start"]) or \
                e.get("DTEND;TZID=Asia/Taipei") != calendar_ics._local(x["end"]):
            problems.append(f"{e.get('UID')} times differ from the model")
        for i in re.findall(r"Evidence: ([^.]+)\.", e.get("DESCRIPTION", "").replace("\\,", ",")):
            problems += [f"{e.get('UID')} unresolved evidence {j}" for j in i.split(", ") if not citations_known(j)]
    if len(vevents) != len(expected):
        problems.append(f"{len(vevents)} events, expected {len(expected)}")
    add("V-ics", "event-calendar.ics", not problems,
        "Calendar is a draft (PUBLISH), events tentative and transparent with stable UIDs, explicit timezone, "
        "no attendees, times equal to the model", problems)

    # Programme
    prog = ri.programme
    problems = []
    if prog["status"] == "planned":
        w = view["window"]
        problems += programme_check(prog["blocks"], datetime.fromisoformat(w["start"]), datetime.fromisoformat(w["end"]))
        pd_ids = {d["id"] for d in prog["decisions"]}
        base = {b["id"]: b for b in ri.decision["baseline"]}
        for b in prog["blocks"]:
            if b["basis"] not in ("source", "planner-decision", "source-duration, planner-placement", "unallocated"):
                problems.append(f"{b['id']} has unknown basis")
            if b["basis"] != "source" and not (set(b["decision_ids"]) and set(b["decision_ids"]) <= pd_ids):
                problems.append(f"{b['id']} lacks a recorded planner decision")
            for e in b["evidence_ids"]:
                if e.startswith("B-") and base.get(e, {}).get("support") != "supported":
                    problems.append(f"{b['id']} rests on unsupported {e}")
        demos = [b for b in prog["blocks"] if b["kind"] == "demo"]
        if len(demos) != prog["demo_count"]:
            problems.append("not every demo is scheduled exactly once")
    add("V-programme", "event-plan.md", not problems,
        "Run of show has no overlaps; every time is a source fact or a recorded Programme planner decision", problems)

    # Evidence, amounts, wording, privacy
    unknown = {name: [i for i in ids if not citations_known(i)] for name, ids in cited.items()}
    add("V-evidence", "event-plan.md", not any(unknown.values()), "Every cited evidence id resolves", unknown)
    bad_amounts = []
    for name, text in files.items():
        for m in TWD.finditer(text):
            if int(m.group(1).replace(",", "")) not in allowed:
                bad_amounts.append(f"{name}: TWD {m.group(1)}")
    for r in body:
        row = dict(zip(header, r))
        for col in ("cost_twd", "vendor_total_twd", "remaining_under_ceiling_twd"):
            if row[col] and int(row[col]) not in allowed:
                bad_amounts.append(f"csv {row['option_id']} {col}={row[col]}")
    add("V-amounts", "vendor-comparison.csv", not bad_amounts, "Every amount shown exists in the model", bad_amounts)
    claims = {name: affirmative_claims(text) for name, text in files.items()}
    add("V-wording", "draft-communications.md", not any(claims.values()),
        "No affirmative claim of booking, confirmation, approval, selection, reservation or commitment",
        {k: v for k, v in claims.items() if v})
    leaks = {name: EMAIL.findall(t) + PHONE.findall(t) for name, t in files.items()}
    add("V-privacy", "draft-communications.md", not any(leaks.values()), "No email addresses or phone numbers",
        {k: v for k, v in leaks.items() if v})
    comms = files["draft-communications.md"]
    sections = comms.count("\n## M")
    add("V-comms-drafts", "draft-communications.md", sections > 0 and comms.count("**UNSENT DRAFT**") == sections,
        "Every message is labelled UNSENT DRAFT", sections)
    return checks
