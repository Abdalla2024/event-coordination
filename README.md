# Event Planning & Coordination

Build a reusable Skill that compares event options and produces consistent planning drafts.

## Implementation

The Agent Skill [`event-planning-coordination-brief`](event-planning-coordination-brief/SKILL.md) produces a review-ready event planning and coordination brief for the Fellowship Demo Day. It:

- reads the stakeholder-disclosed sources and records every retrieval attempt;
- compares the event options the evidence supports;
- evaluates each option's feasibility and records the approvals it still needs;
- produces planning drafts that trace back to the captured evidence.

It is read-only towards the source systems. `SKILL.md` has the detailed workflow and rules; `event-planning-coordination-brief/references/` has the policies behind them.

## Runtime and setup

The project runs on Python 3.11 or newer (developed on 3.13) in a local virtual environment. Dependencies are pinned in [`requirements.txt`](event-planning-coordination-brief/requirements.txt). `icalendar` is marked there as test-only: it parses the generated calendar in the tests, and the calendar itself is written with the standard library.

```bash
python3 -m venv .venv
.venv/bin/pip install -r event-planning-coordination-brief/requirements.txt
```

No credentials are needed; every disclosed source is publicly readable.

## Run

```bash
# End to end: capture, normalize, decide, recommend, plan the run of show, render the deliverables,
# write the nine-snapshot run and update the history
.venv/bin/python event-planning-coordination-brief/scripts/run.py run

# Check the current run, its snapshot chain and its history without changing anything
.venv/bin/python event-planning-coordination-brief/scripts/run.py verify

# Tests
.venv/bin/python -m pytest
```

Both `run` and `verify` write to or check `deliverables/` by default; `--deliverables <dir>` overrides it. For inspection, `run.py render --out <dir>` renders the four drafts and `render-manifest.json` into another directory, without snapshots or history.

| Exit code | Run status | Meaning |
|---|---|---|
| 0 | `complete` | Outputs validated and a justified recommendation produced; approvals still pending |
| 10 | `partial` | Outputs validated, but a business decision needs human judgment, or a source was not retrieved |
| 20 | `blocked` | No option could be built |
| 30 | `failed` | The workflow itself failed; see `deliverables/failure.json` |

The current live scenario exits **10 on purpose**. Neither conditional option is better on every factor, so the recommendation is deferred to Operations.

## Outputs

`deliverables/` holds the current run:

| File | Contents |
|---|---|
| `vendor-comparison.csv` | One row per option: quotes, cost in TWD, feasibility, planning state, evidence, tradeoffs, unresolved items, approval status |
| `event-plan.md` | The review-ready plan: headcount, timing and run of show, budget, options, accessibility evidence, recommendation or deferral, risks, owners, and an evidence index |
| `event-calendar.ics` | A draft calendar of tentative planning blocks |
| `draft-communications.md` | Unsent draft messages to Operations, the budget owners, vendors and attendees |
| `render-manifest.json` | Hashes of the deliverables and the result of each validation check |
| `snapshots/` | The nine linked stage snapshots; `snapshots/evidence/` holds every captured source |
| `current-run.json` | Pointer to the active run: status, snapshot and artifact hashes, supersede and recovery record |
| `history/` | Every earlier run or attempt, retained with the reason it was superseded |

## Current validation

On the committed state:

- 215 tests pass and pyflakes is clean;
- `run.py verify` exits 0;
- the live `run.py run` exits 10, as intended;
- of 7 options, 0 are feasible, 2 are conditional and 5 are infeasible;
- the recommendation is deferred to Operations: lower cost (Q-003 bundle, 494,000 TWD) against a larger catering buffer (Q-004 bundle, 512,000 TWD).

## Interviews

The original Work Sim exports of the three stakeholder interview sessions are stored, unedited, under [`interviews/`](interviews/), as the assignment requires.

## Safety and scope

Generated communications are unsent drafts, and calendar events are tentative. The Skill does not book, pay, send invitations, contact vendors, write to production calendars or grant approvals.

## Assignment context

The sections below are kept from the starter.

## Start

1. Read the [formal assignment](https://private-pecorino-70e.notion.site/Project-C-Event-Planning-Coordination-Brief-Learner-assignment-3da0b700541e813a8a91d0741d6ac96a?source=copy_link) for the work and acceptance requirements.
2. Create your own repository from [this starter](https://github.com/GitRollTraining/event-coordination) using **Fork**, then clone your copy and work there.

## Supplied files

| File | Purpose |
|---|---|
| `README.md` | Starting instructions and links. |
| `snapshot.schema.json` | Public snapshot contract; keep it unchanged. |

Create the Skill, implementation and outputs described in the formal assignment. This starter supplies no business workflow implementation.

## Before you work

**Interview rule.** You conduct the stakeholder interview yourself, and the questions are yours. Do not connect a coding agent or any other AI to the interview to run, script, or automate it. The interview transcript is assessed together with the code; a project whose interview was run by an agent is not scored.

- Export your interview as the original Work Sim Markdown, save one final complete file per session under `interviews/`, and commit and push it with your code. Do not rewrite the export. If the export is unavailable, contact the facilitator.

- Use an Agent Skills-capable coding environment. Choose and document your implementation runtime and dependencies; no runtime or install command is supplied here.
- Follow the [shared course guide for session capture](https://classroom.google.com/c/ODcyMjA4NTkwNDk2/m/ODc0NzI2NzQzMzQ2/details) and verify capture is active before implementation. Keep credentials out of the repository.
- Meet the [stakeholder](https://work-sim.catalyte.ai/s/project-c-event-coordination) to understand the work and relevant business sources. Read those online sources through their intended access route; an unavailable source is not permission to substitute repository data.
