---
name: event-planning-coordination-brief
description: Builds a review-ready, draft-only Demo Day plan for Quillhaven Academy from the stakeholder-disclosed sources (event brief, calendar, budget, attendee signals, vendor register, official TICC venue pages and 4F floor plan). Retrieves every source with each attempt recorded, compares supported options, keeps unconfirmed holds and prerequisites conditional, and writes nine linked snapshots plus comparison, plan, calendar and communication drafts. Never books, pays, invites, commits to vendors, writes production calendars or changes approvals.
---

# Event planning coordination brief

Use this skill to produce or refresh the Fellowship Demo Day planning package. Inputs change at
different times; the skill re-reads every disclosed source on each run and re-derives every
dependent draft, so the drafts stay consistent with each other and with the evidence.

> **Build status: Phase 2 (normalized sources).** Source capture, parsing, normalization into
> evidence-linked claims, decision-rule primitives and the snapshot chain exist and are tested. Option
> evaluation, the nine-stage run and the four drafts are added in later phases.

## Setup

Python 3.11 or newer (developed on 3.13).

```bash
python3 -m venv .venv
.venv/bin/pip install -r event-planning-coordination-brief/requirements.txt
```

No credentials are needed: every disclosed source is publicly readable. Do not add credentials to the repository.

## Commands

```bash
# Retrieve and parse every disclosed source, recording every attempt
.venv/bin/python event-planning-coordination-brief/scripts/run.py capture --out <dir>

# Capture, then normalize every source into evidence-linked claims
.venv/bin/python event-planning-coordination-brief/scripts/run.py normalize --out <dir>

# Tests
.venv/bin/python -m pytest
```

`capture` writes the retrieved bytes to `<dir>/snapshots/evidence/<SOURCE-ID>/<ATTEMPT-ID>.<ext>` and a
`capture-report.json` with one schema `sourceRecord` per source. It exits non-zero if any source is not `retrieved`.
`normalize` also writes `normalized-report.json` with every claim and prints the claims that are not
`supported`. The claim model is described in `references/normalization.md`.

## Workflow (nine stages)

| # | Stage | What happens | Kind |
|---|---|---|---|
| 01 | scope-and-approval-gates | Objective, decision deadline, owners, approval gates | deterministic |
| 02 | source-capture | Every disclosed source retrieved; every attempt, hash and locator recorded | deterministic |
| 03 | constraint-model | Hard constraints, preferences, assumptions, unknowns, conflicts | deterministic, from sources and `references/` |
| 04 | planning-baseline | Headcount by group, schedule dependencies, budget, accessibility | deterministic |
| 05 | option-generation | Option bundles from the quotes; early rejections with reasons | deterministic |
| 06 | feasibility-testing | Checks and classification (`references/decision-policy.md`) | deterministic |
| 07 | decision-and-approval | Recommendation or deferral with tradeoffs; approvals `pending` | **agent reasoning**, validated |
| 08 | draft-propagation | CSV, plan, calendar, communications from one model | deterministic rendering, agent prose |
| 09 | publication-validation | Schema, hash chain, cross-file consistency, privacy and claim scans | deterministic |

## Rules the skill must keep

Read `references/decision-policy.md` before changing any rule. In short:

- **Values come from the sources captured in this run.** No amount, date, capacity or roster is hard-coded. A value that is missing, duplicated or invalid is held, never guessed.
- **Held and available are not confirmations.** An option relying on them, or on an unevidenced prerequisite, is `conditional`. The prerequisites are venue confirmation, accessibility walkthrough, TICC technical and safety briefing, severe-allergy contact coordination and the livestream network test. No option is `feasible` just because its other checks pass, and no second feasible option is ever fabricated.
- **Budget:** an amount within the approval limit passes, with its variance noted. An amount above the limit is `conditional`. A total including the communications and contingency allowances above the ceiling is `infeasible`.
- **Venue cost** uses the negotiated case amount from the vendor register. The official TICC tariff is recorded beside it as a documented difference.
- **The floor plan is spatial evidence only.** Counts and hearing-loop availability come from the coordination record.
- **No invented deadlines.** The TICC briefing stays an Operations action with no date.
- **Drafts only.** Every approval stays `pending` unless an actual human response is recorded. No booking, payment, invitation, vendor commitment, production-calendar write or approval change. No names, contact details or medical details in any output; aggregate counts only.

## Retrieval behaviour

- Each source is read through its disclosed route (`references/sources.json`). Google Sheets are read through the same document's xlsx export. The Notion brief is read through Notion's public page-data endpoint for the disclosed page.
- **TICC pages:** a plain request comes first. Only if the site rejects it is one browser-like retry made, recorded as a separate attempt. Rejected attempts and their response bodies are kept.
- **TLS:** certificate-chain and hostname verification stay on. Python 3.13's extra `VERIFY_X509_STRICT` flag is cleared because the TICC certificate chain lacks a Subject Key Identifier, which that flag rejects.
- **Versions:** sources are identified by exact retrieval timestamp (stakeholder rule), with any native version beside it. A sha256 is recorded for every byte stream as an integrity check.

## Agent reasoning steps

These steps need judgment. Their output is recorded as evidence-cited records and validated by code:

1. **Floor-plan observations** (`references/floorplan-observations.json`). Read the captured 4F PDF and record spatial observations with page and region locators, bound to the PDF's sha256. Mark anything not clearly legible as `ambiguous`. If the captured PDF's hash no longer matches, every observation is held as unverified: render the new PDF, read it again, and update the file and its hash.
2. **Recommendation.** Weigh cost, capacity buffer and other current risks with no fixed weights. Vendor experience is never scored without records.
3. **Prose** for the plan and the unsent draft messages.

## Files

- `references/sources.json`: disclosed sources, routes, meanings, table fields
- `references/requirements-evidence.json`: verbatim stakeholder quotes (STK-*) and assignment requirements (ASG-*)
- `references/decision-policy.md`: the rules above, each traced to its basis
- `references/run-config.json`: business clock, schema path, HTTP profiles
- `references/normalization.md`: claim model, support and evidence statuses, claim kinds
- `references/floorplan-observations.json`: agent-read spatial observations, bound to the PDF hash
- `scripts/run.py`: entry point
- `scripts/coordination/`: capture, sheets, brief, ticc, policy, snapshots
- `scripts/coordination/normalize/`: per-source normalizers, cross-source checks, prerequisites
