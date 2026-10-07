# Deliverables

`scripts/coordination/render/` turns the validated Phase 3 decision model, the Phase 4 recommendation,
the run-of-show plan and the normalized claims into four deliverables and a render manifest. It is
**rendering and packaging only**: it never retrieves, normalizes, decides or recommends, and it never
changes an upstream value. `view.py` is the only module that reads model fields. It maps and labels
them without arithmetic or classification.

## Run of show (`scripts/coordination/programme.py`)

This is a planning step that runs before rendering, and it is allowed to do time arithmetic.

- **Source facts:** setup 07:30–09:30 (readiness record), keynote 10:00–11:00, event window 09:30–17:00, teardown 17:00–18:30, the roster, and the 10 + 3 minute demo durations.
- **Programme planner decisions** (`references/programme-decisions.json`, owner Programme, pending review): opening 15 minutes, lunch 60, two breaks of 15, closing 15, the order, and the demo grouping (two halves around lunch, in roster order). The brief delegates these choices to the planner (`N-BRIEF-planner_schedule_choices`).
- Remaining time is **unallocated Programme buffer**; no activity is invented.
- If an input is unsupported or the plan does not fit, the programme is `unresolved` and has no blocks.

## `vendor-comparison.csv`

One row per Phase 3 option, in model order (never sorted by cost). Lists and objects are JSON.

| Column | From |
|---|---|
| `option_id`, `quote_ids`, `feasibility` | Phase 3 option |
| `planning_people` | `B-headcount.total` |
| `cost_twd`, `currency` | Phase 3 `total_with_allowances_twd` (the amount checked against the ceiling); blank when the model could not state it, with the reason in `unresolved` |
| `availability_status` | Per quote: status and planning state ("held (planning state, not confirmed)"); service gaps listed |
| `evidence_ids` | Phase 3 option evidence (check ids and derivation) |
| `tradeoffs` | Phase 4 factor results for candidates; `[]` for excluded options |
| `unresolved` | The option's open and unverified checks with owners; the cost reason |
| `approval_status` | The option's approvals (always `pending`) |
| `option_label`, `feasibility_reason`, `quote_details`, `vendor_total_twd`, `allowances_twd`, `remaining_under_ceiling_twd`, `recommendation_outcome` | Extra columns after the 11 required ones |

## `event-plan.md`

The opening banner states the run status, the counts of feasible and conditional options, the Phase 4
outcome, and that nothing has been booked, approved, committed or confirmed.

The sections, in order:
1. Objective
2. Source and run basis
3. Headcount and uncertainty policy
4. Timing, run of show and dependencies
5. Budget and costs (the case venue amount and the official tariff appear separately)
6. Option comparison and feasibility
7. Accessibility and safety evidence and limits (floor-plan region locators)
8. Recommendation or deferral
9. Feasible-option shortfall
10. Risks
11. Unknowns
12. Change impacts (derived from the evidence links)
13. Owners, approvals and review requests

An evidence-index appendix follows. Facts are labelled as source facts, planning states or planner
decisions, or "not established".

## `event-calendar.ics`

- Structure: `VERSION:2.0`, `METHOD:PUBLISH`, and an `Asia/Taipei` time-zone definition (fixed +08:00).
- Every event is `STATUS:TENTATIVE`, `TRANSP:TRANSPARENT` and `CATEGORIES:PLANNING-DRAFT`, with a stable `UID` (`<record>-<date>@event-planning-coordination-brief`). `DTSTAMP` is the run completion time.
- No `ATTENDEE` or `ORGANIZER` fields.
- Each description begins "PROPOSED - NOT BOOKED OR CONFIRMED" and lists the open conditions and evidence.
- **Emitted:** the event window, run-of-show blocks (not buffers), the accessibility walkthrough, and the rehearsal.
- **Not emitted:**
  - the decision deadline and the venue-hold expiry (they are plan items);
  - the infeasible 24 October fallback;
  - the TICC briefing (it has no date);
  - anything for a blocked run or a run with no viable option. In those cases the calendar is empty but still valid.

## `draft-communications.md`

Every message is headed **UNSENT DRAFT** and gives:
- the audience (a role, or the vendor business name from the quote);
- the purpose;
- the conditions before sending;
- the approval owner;
- an evidence basis.

There are no personal names, contact details or invented deadlines.

Messages:
1. Operations: plan review and the deferred decision.
2. One per budget owner: category cost, remaining room under the ceiling, quote validity. The Programme message also asks for review of the planner decisions.
3. Learner Experience: the walkthrough, which can happen only after venue confirmation.
4. One confirmation request per vendor quote used by a candidate option. Each states that it is not a booking or commitment. Vendors of infeasible options are not contacted.
5. One aggregate attendee acknowledgement that promises no date or venue.

## Traceability

The deliverables cite existing ids only (`OPT-`, `CHK-`, `B-`, `N-`/`X-`/`P-`, `TO-`, `DEC-`, `APR-`,
`PRG-`, `PD-`, `STK-`, `ASG-`, source ids):
- **CSV:** the `evidence_ids` column.
- **Plan:** an `_Evidence: …_` line on each row or section, plus the appendix, which resolves each id to its source, locator and retrieval time, or to the model record or stakeholder line.
- **ICS:** evidence ids in each description.
- **Communications:** a basis line per message.

## Render manifest and validation (`render-manifest.json`)

The manifest records:
- artifact paths and sha256 (the shape of the schema `artifactRecord`);
- the sha256 of each input (sources, claims, decision, recommendation, run status, programme);
- the cited ids, the impact map and the programme status;
- the validation checks.

The validation checks:

| Check | What it verifies |
|---|---|
| `V-csv-columns`, `V-csv-rows` | Column order; rows equal the model options; status, cost and approvals equal Phase 3; outcome equals Phase 4; JSON cells; integers; evidence resolves |
| `V-plan-sections`, `V-plan-banner`, `V-recommendation-match` | Sections, banner, and the Phase 4 recommendation |
| `V-ics` | Structure, tentative/transparent, UIDs, explicit time zone, no attendees, times equal to the model |
| `V-programme` | No overlaps; every time is a source fact or a recorded planner decision; every demo exactly once |
| `V-evidence` | Every cited id resolves |
| `V-amounts` | Every TWD amount exists in the model |
| `V-wording` | No affirmative booked/confirmed/approved/selected/secured/reserved/committed statement. Only one exact scope phrase about the readiness record is allowed |
| `V-privacy` | No email addresses or phone numbers |
| `V-comms-drafts` | Every message is labelled UNSENT DRAFT |
| `V-no-mutation` | Upstream inputs are unchanged by rendering |
| `V-file-*` | Written bytes equal the rendered text |
