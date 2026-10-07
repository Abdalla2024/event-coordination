---
name: event-planning-coordination-brief
description: Builds a review-ready, draft-only Demo Day plan for Quillhaven Academy from the stakeholder-disclosed sources (event brief, calendar, budget, attendee signals, vendor register, official TICC venue pages and 4F floor plan). Retrieves every source with each attempt recorded, compares supported options, keeps unconfirmed holds and prerequisites conditional, and writes nine linked snapshots plus comparison, plan, calendar and communication drafts. Never books, pays, invites, commits to vendors, writes production calendars or changes approvals.
---

# Event planning coordination brief

Use this skill to produce or refresh the Fellowship Demo Day planning package. Inputs change at
different times; the skill re-reads every disclosed source on each run and re-derives every
dependent draft, so the drafts stay consistent with each other and with the evidence.

## Setup

Python 3.11 or newer (developed on 3.13).

```bash
python3 -m venv .venv
.venv/bin/pip install -r event-planning-coordination-brief/requirements.txt
```

No credentials are needed: every disclosed source is publicly readable. Do not add credentials to the repository.

## Run

```bash
# End to end: capture -> normalize -> decide -> recommend -> run of show -> deliverables -> nine snapshots
.venv/bin/python event-planning-coordination-brief/scripts/run.py run

# Check the current run, its snapshot chain and history without changing anything
.venv/bin/python event-planning-coordination-brief/scripts/run.py verify
```

Both default to `deliverables/` at the repository root (`--deliverables <dir>` overrides it).

| Exit code | Run status | Meaning |
|---|---|---|
| 0 | `complete` | Validated outputs and a justified recommendation; approvals still pending |
| 10 | `partial` | Validated outputs, but a business decision needs human judgment or a source was not retrieved |
| 20 | `blocked` | No option could be built; nine snapshots, an explanatory plan, an empty calendar and clarification drafts |
| 30 | `failed` | The workflow itself failed; see `deliverables/failure.json` |

A non-zero exit for `partial` is expected when Operations must still decide.

## Outputs and history

```
deliverables/
├── current-run.json        pointer to the active run: status, snapshot and artifact hashes, supersede and recovery record
├── snapshots/01-…09-….json  the nine linked snapshots; snapshots/evidence/ holds every captured byte stream
├── vendor-comparison.csv, event-plan.md, event-calendar.ics, draft-communications.md, render-manifest.json
├── failure.json            only when the active run failed
└── history/index.json, history/<id>/   every earlier run or attempt, with archive.json
```

- **Staging and promotion.** A run is built in `deliverables/.staging/<run_id>/` and promoted only after the deliverables validate and the nine-snapshot chain verifies. `current-run.json` is written last.
- **Supersede.** The previous run moves to `history/<run_id>/`. Snapshot 01 records `supersedes_run_id`, the changed source and decision ids, and the reason. Material change is judged on each source's interpreted observations and the decision outcome; raw download bytes can differ between identical exports. Promotion is refused if the active run changed during the run, so an older run never replaces a newer one.
- **Recovery.** At start, the run checks the existing state. An interrupted attempt (`.in-progress.json` left behind) is preserved as `history/<run_id>-attempt/` and never promoted. Current outputs that fail verification (hash, chain or manifest) are preserved as history and marked `invalid`. The new run then supersedes the latest valid run. Recovery re-captures the sources; it never reuses partial outputs and never changes a decision.
- **Failure.** Any stage error, deliverable validation failure or chain failure writes `failure.json`. It contains: run id, `observed_at`, affected stage, classification, sanitized error, available evidence (attempts with their real retrieval states), affected artifacts, recovery record, `next_owner` and recovery action. The failed attempt is preserved in history. Earlier outputs are moved to history, so they are not presented as the current result.

## Inspection commands

```bash
# Retrieve and parse every disclosed source, recording every attempt
.venv/bin/python event-planning-coordination-brief/scripts/run.py capture --out <dir>

# Capture, then normalize every source into evidence-linked claims
.venv/bin/python event-planning-coordination-brief/scripts/run.py normalize --out <dir>

# Capture, normalize, then build the feasibility model (no deliverables)
.venv/bin/python event-planning-coordination-brief/scripts/run.py decide --out <dir>

# Decide, then compare the non-infeasible options and report the run status (no deliverables)
.venv/bin/python event-planning-coordination-brief/scripts/run.py recommend --out <dir>

# Recommend, plan the run of show, render and validate the four deliverables + render-manifest.json
.venv/bin/python event-planning-coordination-brief/scripts/run.py render --out <dir>

# Tests
.venv/bin/python -m pytest
```

`capture` writes the retrieved bytes to `<dir>/snapshots/evidence/<SOURCE-ID>/<ATTEMPT-ID>.<ext>` and a
`capture-report.json` with one schema `sourceRecord` per source. It exits non-zero if any source is not `retrieved`.
`normalize` also writes `normalized-report.json` with every claim and prints the claims that are not
`supported`. The claim model is described in `references/normalization.md`.
`decide` also writes `decision-report.json`: the baseline, every option with its checks, costs and
classification, approvals, dependencies, unresolved items and comparison facts
(`references/decision-model.md`).
`recommend` also writes `recommendation-report.json`: the recommendation outcome, factor comparisons,
the question for Operations when the choice is deferred, and the run status
(`references/recommendation-policy.md`).
`render` writes `vendor-comparison.csv`, `event-plan.md`, `event-calendar.ics`, `draft-communications.md`
and `render-manifest.json` (artifact hashes and validation checks) to `<dir>`, and exits non-zero if any
validation check fails (`references/deliverables.md`).

## Workflow (nine stages)

| # | Stage | What happens | Kind |
|---|---|---|---|
| 01 | scope-and-approval-gates | Objective, decision deadline, owners, approval gates | deterministic |
| 02 | source-capture | Every disclosed source retrieved; every attempt, hash and locator recorded | deterministic |
| 03 | constraint-model | Hard constraints, preferences, assumptions, unknowns, conflicts | deterministic, from sources and `references/` |
| 04 | planning-baseline | Headcount by group, schedule dependencies, budget, accessibility | deterministic |
| 05 | option-generation | Option bundles from the quotes; early rejections with reasons | deterministic |
| 06 | feasibility-testing | Checks and classification (`references/decision-policy.md`) | deterministic |
| 07 | decision-and-approval | Recommendation by dominance only, or deferral to Operations with the tradeoff stated; approvals `pending` | deterministic (no weights) |
| 08 | draft-propagation | Run of show (Programme planner decisions labelled), then CSV, plan, calendar, communications from one model | deterministic |
| 09 | publication-validation | Final artifact paths and hashes, deliverable validation checks, publication status | deterministic |

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

## Judgment inputs

These inputs need judgment rather than code. Each is kept as a reference file, cited as evidence, and validated by code:

1. **Floor-plan observations** (`references/floorplan-observations.json`). Read the captured 4F PDF and record spatial observations with page and region locators, bound to the PDF's sha256. Mark anything not clearly legible as `ambiguous`. If the captured PDF's hash no longer matches, every observation is held as unverified: render the new PDF, read it again, and update the file and its hash.
2. **Programme planner decisions** (`references/programme-decisions.json`). Durations the sources do not give (opening, lunch, breaks, closing), order and grouping are set by the planner, owned by Programme and pending its review. They are labelled as planner decisions everywhere they appear, never as source facts.

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
- `references/decision-model.md`: baseline, option generation, check catalogue, costs, outputs
- `scripts/coordination/decide/`: baseline, options and costs, checks, decision model
- `references/recommendation-policy.md`: candidates, factors, dominance, outcomes, run status
- `scripts/coordination/recommend.py`: recommendation layer and run status
- `references/programme-decisions.json`: Programme planner decisions for the run of show
- `references/deliverables.md`: deliverable contents, field mapping, traceability, validation
- `scripts/coordination/programme.py`: run-of-show planning (non-overlapping, buffers explicit)
- `scripts/coordination/render/`: view model, CSV/plan/ICS/communications renderers, impact, validation
- `scripts/coordination/stages.py`: the nine snapshots, packaged from the phase outputs
- `scripts/coordination/history.py`: current-run pointer, history index, archive, promotion, verification
- `scripts/coordination/pipeline.py`: the end-to-end run, recovery and `failure.json`
