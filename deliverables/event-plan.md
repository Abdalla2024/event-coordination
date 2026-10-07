# Quillhaven AI Fellowship Demo Day — planning draft

> **DRAFT FOR REVIEW — run status `partial`** (recommendation outcome 'deferred-to-operations' requires Operations judgment).
> Feasible options: 0. Conditional options: 2 (OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004).
> Recommendation outcome: **`deferred-to-operations`**. No option is recommended. The choice is deferred to Operations.
> Nothing has been booked, approved, committed or confirmed. Every approval is pending.

## 1. Objective and success criteria

- **Event (source fact):** Quillhaven AI Fellowship Demo Day at Taipei International Convention Center. _Evidence: N-BRIEF-event_name, N-BRIEF-venue_name_
- **Preferred date (source fact):** 2026-10-17, 09:30–17:00. _Evidence: B-event-window_
- **Success criteria (source facts):** at least 80% of registered attendees check in; all scheduled fellow demos run; accessibility requests receive a documented response before the event. _Evidence: N-BRIEF-checkin_target_percent, N-BRIEF-success_all_demos_run, N-BRIEF-success_accessibility_response_before_event_

## 2. Source and run basis

- Run `run-20261007T212022Z-a4b5ed`, rendered from the run completed at 2026-10-07T21:20:30.043Z. Business clock 2026-08-26T12:00:00+08:00 (quote and hold validity are judged at this clock). _Evidence: ASG-CLOCK_
- Unversioned sources are identified by retrieval timestamp; native versions are shown where the source has one. _Evidence: STK-I3-L181_

| Source | Status | Retrieved at | Native version |
|---|---|---|---|
| `SRC-BRIEF` Project C event brief (Notion page) | retrieved | 2026-10-07T21:20:22.451Z | brief_version=EVENT-BRIEF-2026-08-26, venue_record=VEN-2026-08-26, venue_clarification=VEN-2026-08-26-R2, programme_clarification=PROG-2026-08-26-R3, notion_last_edited=2026-09-13T19:18:39.915000Z, notion_page_version=44 |
| `SRC-CALENDAR` Project C — Calendar Constraints (Google Sheet) | retrieved | 2026-10-07T21:20:22.884Z | record_version=['calendar-2026-08-26'] |
| `SRC-BUDGET` Project C — Budget (Google Sheet) | retrieved | 2026-10-07T21:20:23.370Z | record_version=['budget-2026-08-26'] |
| `SRC-ATTENDEE` Project C — Attendee Signals (Google Sheet) | retrieved | 2026-10-07T21:20:23.806Z | none |
| `SRC-VENDOR` Project C — Vendor Quotes (Google Sheet) | retrieved | 2026-10-07T21:20:24.281Z | none |
| `SRC-TICC-HALL` TICC official Plenary Hall venue page | retrieved | 2026-10-07T21:20:25.437Z | none |
| `SRC-TICC-ACCESS` TICC official accessibility index (accessible facilities floor plans) | retrieved | 2026-10-07T21:20:26.510Z | none |
| `SRC-TICC-4F` TICC official 4F accessible facilities floor plan (PDF) | retrieved | 2026-10-07T21:20:30.017Z | page_count=1, pdf_mod_date=2024-03-15T05:38:57Z |

## 3. Headcount and uncertainty policy

**Planning headcount (source facts, separate groups):**

| Group | People |
|---|---|
| fellows | 148 |
| partners | 32 |
| staff | 18 |
| speakers | 12 |
| walk_ins | 35 |
| **Total** | **245** |

_Evidence: B-headcount, STK-I1-L41, STK-I1-L87_

**Overlapping needs (counted within the groups, never added):**

| Need | Count |
|---|---|
| wheelchair seating | 6 |
| mobility companion | 4 |
| live captions | 23 |
| hearing loop | 7 |
| quiet room | 9 |
| vegetarian meal | 28 |
| halal meal | 12 |
| severe allergy follow up | 4 |

_Evidence: B-need-wheelchair_seating, B-need-mobility_companion, B-need-live_captions, B-need-hearing_loop, B-need-quiet_room, B-need-vegetarian_meal, B-need-halal_meal, B-need-severe_allergy_follow_up_

- The walk-in figure (35) is a forecast at **medium** confidence. _Evidence: N-ATT-group-walk_ins_
- **Uncertainty policy:** values are read from the captured sources. Missing, conflicting or invalid values are held, not guessed. `held` and `available` are planning states, not confirmations. An option with any open hard dependency is `conditional`, not feasible. _Evidence: ASG-CHANGED-INPUTS, STK-I3-L25, STK-I3-L49, N-BRIEF-conditional_not_feasible_rule_

## 4. Timing, run of show and dependencies

**Calendar facts (source facts; a hold is a planning state, not a booking):**

| Item | When | Note |
|---|---|---|
| Preferred event window | 2026-10-17 09:30–17:00 | priority hard _Evidence: B-event-window_ |
| Fallback event window | 2026-10-24 09:30–17:00 | priority soft _Evidence: B-fallback-window_ |
| Keynote availability | 2026-10-17 10:00–11:00 | priority hard _Evidence: B-keynote_ |
| Venue hold (planning state) | 2026-10-17 07:30–18:30 | priority hard _Evidence: B-venue-hold_ |
| Teardown window | 2026-10-17 17:00–18:30 | priority hard _Evidence: B-teardown_ |
| Plan and budget decision deadline | 2026-09-04 17:00 | decision item, not a calendar event _Evidence: B-decision-deadline_ |
| Accessibility walkthrough | 2026-09-25 14:00–16:00 | owner Learner Experience, hard; Venue confirmation required first _Evidence: N-CAL-CAL-006_ |
| Rehearsal window | 2026-10-16 15:00–18:00 | owner Programme, soft; Remote backup acceptable _Evidence: N-CAL-CAL-007_ |
| Venue hold expiry | 2026-09-05 | planning dependency, not an event; _Evidence: X-hold-vs-deadline_ |

**Run of show (proposed):**

Block durations for the demos, keynote, setup and teardown are **source facts**. Opening, lunch, break and closing durations, the order and the demo grouping are **Programme planner decisions** (pending Programme review). Unallocated time is shown as buffer; no activity is invented. _Evidence: N-BRIEF-planner_schedule_choices, B-programme_

| Time | Block | Basis |
|---|---|---|
| 07:30–09:30 | Setup and pre-opening readiness checks | source fact _Evidence: PRG-01-setup_ |
| 09:30–09:45 | Opening and welcome | **planner decision** _Evidence: PRG-02-opening_ |
| 09:45–10:00 | Unallocated Programme buffer | unallocated Programme buffer _Evidence: PRG-03-buffer_ |
| 10:00–11:00 | Keynote | source fact _Evidence: PRG-04-keynote_ |
| 11:00–11:15 | Break 1 | **planner decision** _Evidence: PRG-05-break_ |
| 11:15–11:25 | DEMO-01 presentation | source duration, planner placement _Evidence: PRG-06-demo_ |
| 11:25–11:28 | DEMO-01 changeover | source duration, planner placement _Evidence: PRG-07-changeover_ |
| 11:28–11:38 | DEMO-02 presentation | source duration, planner placement _Evidence: PRG-08-demo_ |
| 11:38–11:41 | DEMO-02 changeover | source duration, planner placement _Evidence: PRG-09-changeover_ |
| 11:41–11:51 | DEMO-03 presentation | source duration, planner placement _Evidence: PRG-10-demo_ |
| 11:51–11:54 | DEMO-03 changeover | source duration, planner placement _Evidence: PRG-11-changeover_ |
| 11:54–12:04 | DEMO-04 presentation | source duration, planner placement _Evidence: PRG-12-demo_ |
| 12:04–12:07 | DEMO-04 changeover | source duration, planner placement _Evidence: PRG-13-changeover_ |
| 12:07–12:17 | DEMO-05 presentation | source duration, planner placement _Evidence: PRG-14-demo_ |
| 12:17–12:20 | DEMO-05 changeover | source duration, planner placement _Evidence: PRG-15-changeover_ |
| 12:20–12:30 | DEMO-06 presentation | source duration, planner placement _Evidence: PRG-16-demo_ |
| 12:30–12:33 | DEMO-06 changeover | source duration, planner placement _Evidence: PRG-17-changeover_ |
| 12:33–13:33 | Lunch | **planner decision** _Evidence: PRG-18-lunch_ |
| 13:33–13:43 | DEMO-07 presentation | source duration, planner placement _Evidence: PRG-19-demo_ |
| 13:43–13:46 | DEMO-07 changeover | source duration, planner placement _Evidence: PRG-20-changeover_ |
| 13:46–13:56 | DEMO-08 presentation | source duration, planner placement _Evidence: PRG-21-demo_ |
| 13:56–13:59 | DEMO-08 changeover | source duration, planner placement _Evidence: PRG-22-changeover_ |
| 13:59–14:09 | DEMO-09 presentation | source duration, planner placement _Evidence: PRG-23-demo_ |
| 14:09–14:12 | DEMO-09 changeover | source duration, planner placement _Evidence: PRG-24-changeover_ |
| 14:12–14:22 | DEMO-10 presentation | source duration, planner placement _Evidence: PRG-25-demo_ |
| 14:22–14:25 | DEMO-10 changeover | source duration, planner placement _Evidence: PRG-26-changeover_ |
| 14:25–14:35 | DEMO-11 presentation | source duration, planner placement _Evidence: PRG-27-demo_ |
| 14:35–14:38 | DEMO-11 changeover | source duration, planner placement _Evidence: PRG-28-changeover_ |
| 14:38–14:48 | DEMO-12 presentation | source duration, planner placement _Evidence: PRG-29-demo_ |
| 14:48–14:51 | DEMO-12 changeover | source duration, planner placement _Evidence: PRG-30-changeover_ |
| 14:51–15:06 | Break 2 | **planner decision** _Evidence: PRG-31-break_ |
| 15:06–16:45 | Unallocated Programme buffer | unallocated Programme buffer _Evidence: PRG-32-buffer_ |
| 16:45–17:00 | Closing | **planner decision** _Evidence: PRG-33-closing_ |
| 17:00–18:30 | Teardown; all vendors clear | source fact _Evidence: PRG-34-teardown_ |

Unallocated Programme buffer: 114 minutes. All 12 demos are included once.

**Programme planner decisions:**

- `PD-opening-minutes`: Opening/welcome lasts 15 minutes, starting at the event window opening. (owner Programme; planner decision, pending Programme review) _Evidence: PD-opening-minutes, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_
- `PD-lunch-minutes`: Lunch lasts 60 minutes. (owner Programme; planner decision, pending Programme review) _Evidence: PD-lunch-minutes, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_
- `PD-break-minutes`: Each of the two breaks lasts 15 minutes. (owner Programme; planner decision, pending Programme review) _Evidence: PD-break-minutes, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_
- `PD-break-count`: Two breaks, matching the quoted catering package (lunch and two breaks). (owner Programme; planner decision, pending Programme review) _Evidence: PD-break-count, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_
- `PD-closing-minutes`: Closing lasts 15 minutes and ends at the event window close. (owner Programme; planner decision, pending Programme review) _Evidence: PD-closing-minutes, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_
- `PD-order`: Order: opening; keynote at its fixed time; break 1; first half of the demos (roster order); lunch; second half of the demos (roster order); break 2; closing at the end of the window. Any remaining time is unallocated Programme buffer, not invented content. (owner Programme; planner decision, pending Programme review) _Evidence: PD-order, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_
- `PD-demo-grouping`: Demos are split into two groups around lunch; the first group takes the larger half when the count is odd, and roster order is kept. (owner Programme; planner decision, pending Programme review) _Evidence: PD-demo-grouping, N-BRIEF-planner_schedule_choices, N-BRIEF-roster_change_owner_

**Dependencies (no deadline is invented where none is stated):**

| Dependency | Outcome | Owner | Affected options |
|---|---|---|---|
| Q-003 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Operations | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008 _Evidence: DEP-Q-003-confirmation_ |
| Q-005 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Learner Experience | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-Q-005-confirmation_ |
| Q-006 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Programme | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-Q-006-confirmation_ |
| Q-009 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Operations | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-Q-009-confirmation_ |
| Q-010 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Learner Experience | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-Q-010-confirmation_ |
| Venue confirmation: required condition with no evidence of completion. | open | Operations | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-24-fallback _Evidence: DEP-P-venue-confirmation_ |
| Accessibility walkthrough: required condition with no evidence of completion. Depends on ['P-venue-confirmation']. | open | Learner Experience | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-24-fallback _Evidence: DEP-P-accessibility-walkthrough_ |
| TICC technical coordination meeting and safety evacuation briefing: required condition with no evidence of completion. | open | Operations | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-24-fallback _Evidence: DEP-P-ticc-technical-safety-briefing_ |
| Severe-allergy contact coordination: required condition with no evidence of completion. | open | Operations | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-P-severe-allergy-contacts_ |
| Q-004 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Operations | OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-Q-004-confirmation_ |
| Readiness by 09:30 and clearance by 18:30 is not confirmed for ['Q-007']; no vendor durations are given, so it cannot be derived. | unverified | Operations | OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-24-fallback _Evidence: DEP-readiness_ |
| Q-007 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. | open | Programme | OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004-sub-Q-007 _Evidence: DEP-Q-007-confirmation_ |
| Q-008 is 'conditional': an outstanding required condition must be resolved. | open | Programme | OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-Q-008-confirmation_ |
| Livestream network test for Q-008: required condition with no evidence of completion. | open | Operations | OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-P-livestream-network-test-Q-008_ |
| Venue confirmation for livestream Q-008: required condition with no evidence of completion. | open | Operations | OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-P-livestream-venue-confirmation-Q-008_ |
| production: 133000 exceeds approval limit 100000 (variance from planned 85000: +48000); explicit approval by Programme required. | open | Programme | OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-004-add-Q-008 _Evidence: DEP-budget-production_ |
| No accessibility quote is available on 2026-10-24; availability cannot be assumed. | unverified | Operations | OPT-2026-10-24-fallback _Evidence: DEP-service-accessibility_ |
| No catering quote is available on 2026-10-24; availability cannot be assumed. | unverified | Operations | OPT-2026-10-24-fallback _Evidence: DEP-service-catering_ |
| No production quote is available on 2026-10-24; availability cannot be assumed. | unverified | Operations | OPT-2026-10-24-fallback _Evidence: DEP-service-production_ |
| No security quote is available on 2026-10-24; availability cannot be assumed. | unverified | Operations | OPT-2026-10-24-fallback _Evidence: DEP-service-security_ |
| No quote in this option provides hearing loop. | unverified | Learner Experience | OPT-2026-10-24-fallback _Evidence: DEP-access-hearing_loop_ |
| No quote in this option provides live captions. | unverified | Learner Experience | OPT-2026-10-24-fallback _Evidence: DEP-access-live_captions_ |
| No quiet-room staffing in this option. | unverified | Learner Experience | OPT-2026-10-24-fallback _Evidence: DEP-access-staffed_quiet_room_ |
| Total cost cannot be stated: no quotes for ['accessibility', 'catering', 'production', 'security'] on 2026-10-24. | unverified | Operations | OPT-2026-10-24-fallback _Evidence: DEP-budget-ceiling_ |

## 5. Budget and costs

- **Planning ceiling (source fact):** TWD 520,000, including the communications and contingency allowances. _Evidence: B-ceiling, B-allowances, STK-I2-L53_
- **Allowances (source facts):** communications TWD 25,000, contingency TWD 40,000. _Evidence: B-allowances_
- **Venue amount:** Planning uses the negotiated case amount TWD 155000 (Q-001, full-day package). The official published weekend rate is TWD 170000 per time slot. The amounts are not comparable one-for-one and the case amount is not replaced. _Evidence: NOTE-venue-tariff, STK-I3-L205_

| Category | Planned | Approval limit | Owner |
|---|---|---|---|
| venue | TWD 155,000 | TWD 180,000 | Operations |
| catering | TWD 115,000 | TWD 135,000 | Operations |
| accessibility | TWD 65,000 | TWD 80,000 | Learner Experience |
| production | TWD 85,000 | TWD 100,000 | Programme |
| communications | TWD 25,000 | TWD 30,000 | Communications |
| security | TWD 25,000 | TWD 35,000 | Operations |
| contingency | TWD 40,000 | TWD 50,000 | Operations |

_Evidence: B-budget-venue, B-budget-catering, B-budget-accessibility, B-budget-production, B-budget-communications, B-budget-security, B-budget-contingency_

**OPT-2026-10-17-Q-003 (conditional)** — category amounts and checks:

| Category | Amount | Check |
|---|---|---|
| accessibility | TWD 60,000 | pass: accessibility: 60000 within approval limit 80000 (variance from planned 65000: -5000); ordinary approval by Learner Experience still pending. _Evidence: CHK-OPT-2026-10-17-Q-003-budget-accessibility_ |
| catering | TWD 108,000 | pass: catering: 108000 within approval limit 135000 (variance from planned 115000: -7000); ordinary approval by Operations still pending. _Evidence: CHK-OPT-2026-10-17-Q-003-budget-catering_ |
| production | TWD 78,000 | pass: production: 78000 within approval limit 100000 (variance from planned 85000: -7000); ordinary approval by Programme still pending. _Evidence: CHK-OPT-2026-10-17-Q-003-budget-production_ |
| security | TWD 28,000 | pass: security: 28000 within approval limit 35000 (variance from planned 25000: +3000); ordinary approval by Operations still pending. _Evidence: CHK-OPT-2026-10-17-Q-003-budget-security_ |
| venue | TWD 155,000 | pass: venue: 155000 within approval limit 180000 (equal to planned); ordinary approval by Operations still pending. _Evidence: CHK-OPT-2026-10-17-Q-003-budget-venue_ |
| allowances | communications TWD 25,000, contingency TWD 40,000 | counted in the ceiling |
| **Total incl. allowances** | **TWD 494,000** | remaining under ceiling TWD 26,000 _Evidence: CHK-OPT-2026-10-17-Q-003-budget-ceiling_ |

**OPT-2026-10-17-Q-004 (conditional)** — category amounts and checks:

| Category | Amount | Check |
|---|---|---|
| accessibility | TWD 60,000 | pass: accessibility: 60000 within approval limit 80000 (variance from planned 65000: -5000); ordinary approval by Learner Experience still pending. _Evidence: CHK-OPT-2026-10-17-Q-004-budget-accessibility_ |
| catering | TWD 126,000 | pass: catering: 126000 within approval limit 135000 (variance from planned 115000: +11000); ordinary approval by Operations still pending. _Evidence: CHK-OPT-2026-10-17-Q-004-budget-catering_ |
| production | TWD 78,000 | pass: production: 78000 within approval limit 100000 (variance from planned 85000: -7000); ordinary approval by Programme still pending. _Evidence: CHK-OPT-2026-10-17-Q-004-budget-production_ |
| security | TWD 28,000 | pass: security: 28000 within approval limit 35000 (variance from planned 25000: +3000); ordinary approval by Operations still pending. _Evidence: CHK-OPT-2026-10-17-Q-004-budget-security_ |
| venue | TWD 155,000 | pass: venue: 155000 within approval limit 180000 (equal to planned); ordinary approval by Operations still pending. _Evidence: CHK-OPT-2026-10-17-Q-004-budget-venue_ |
| allowances | communications TWD 25,000, contingency TWD 40,000 | counted in the ceiling |
| **Total incl. allowances** | **TWD 512,000** | remaining under ceiling TWD 8,000 _Evidence: CHK-OPT-2026-10-17-Q-004-budget-ceiling_ |

## 6. Option comparison and feasibility

| Option | Status | Total incl. allowances | Reason |
|---|---|---|---|
| `OPT-2026-10-17-Q-003` 2026-10-17 base bundle with catering Q-003 | **conditional** | TWD 494,000 | conditional: Q-003 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-005 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-006 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-009 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-010 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Venue confirmation: required condition with no evidence of completion. / Accessibility walkthrough: required condition with no evidence of completion. Depends on ['P-venue-confirmation']. / TICC technical coordination meeting and safety evacuation briefing: required condition with no evidence of completion. / Severe-allergy contact coordination: required condition with no evidence of completion. _Evidence: OPT-2026-10-17-Q-003_ |
| `OPT-2026-10-17-Q-004` 2026-10-17 base bundle with catering Q-004 | **conditional** | TWD 512,000 | conditional: Q-004 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-005 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-006 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-009 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Q-010 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. / Venue confirmation: required condition with no evidence of completion. / Accessibility walkthrough: required condition with no evidence of completion. Depends on ['P-venue-confirmation']. / TICC technical coordination meeting and safety evacuation briefing: required condition with no evidence of completion. / Severe-allergy contact coordination: required condition with no evidence of completion. _Evidence: OPT-2026-10-17-Q-004_ |
| `OPT-2026-10-17-Q-003-sub-Q-007` 2026-10-17 base bundle with catering Q-003, Q-007 instead of Q-006 | **infeasible** | TWD 468,000 | infeasible: Hearing loop is a hard requirement and ['Q-007'] explicitly excludes it; no other quote in this option provides it. Accessibility cannot be traded away. _Evidence: OPT-2026-10-17-Q-003-sub-Q-007_ |
| `OPT-2026-10-17-Q-003-add-Q-008` 2026-10-17 base bundle with catering Q-003 plus add-on Q-008 | **infeasible** | TWD 549,000 | infeasible: Total 549000 including allowances exceeds the ceiling 520000 by 29000. _Evidence: OPT-2026-10-17-Q-003-add-Q-008_ |
| `OPT-2026-10-17-Q-004-sub-Q-007` 2026-10-17 base bundle with catering Q-004, Q-007 instead of Q-006 | **infeasible** | TWD 486,000 | infeasible: Hearing loop is a hard requirement and ['Q-007'] explicitly excludes it; no other quote in this option provides it. Accessibility cannot be traded away. _Evidence: OPT-2026-10-17-Q-004-sub-Q-007_ |
| `OPT-2026-10-17-Q-004-add-Q-008` 2026-10-17 base bundle with catering Q-004 plus add-on Q-008 | **infeasible** | TWD 567,000 | infeasible: Total 567000 including allowances exceeds the ceiling 520000 by 47000. _Evidence: OPT-2026-10-17-Q-004-add-Q-008_ |
| `OPT-2026-10-24-fallback` 2026-10-24 fallback date | **infeasible** | not stated (no quotes for ['accessibility', 'catering', 'production', 'security'] on 2026-10-24) | infeasible: The hard keynote constraint is only available on 2026-10-17; on 2026-10-24 the keynote is unavailable. _Evidence: OPT-2026-10-24-fallback_ |

**Quotes in the conditional options (planning states; no quote is confirmed):**

| Quote | Vendor | Category | Package | Amount | Capacity | Date | Valid until | Planning state |
|---|---|---|---|---|---|---|---|---|
| Q-001 | TICC | venue | 4F Plenary Hall front-500 allocation plus V.I.P. Room | TWD 155,000 | 500 | 2026-10-17 | 2026-09-05 | held (planning state, not confirmed) _Evidence: N-QUOTE-Q-001_ |
| Q-003 | Green Table | catering | lunch and two breaks | TWD 108,000 | 260 | 2026-10-17 | 2026-09-07 | available (planning state, not confirmed) _Evidence: N-QUOTE-Q-003_ |
| Q-005 | ClearText | accessibility | live captions and transcript | TWD 42,000 | 500 | 2026-10-17 | 2026-09-10 | available (planning state, not confirmed) _Evidence: N-QUOTE-Q-005_ |
| Q-006 | SoundArc | production | AV package with hearing loop | TWD 78,000 | 500 | 2026-10-17 | 2026-09-08 | available (planning state, not confirmed) _Evidence: N-QUOTE-Q-006_ |
| Q-009 | SafeVenue | security | four staff | TWD 28,000 | 500 | 2026-10-17 | 2026-09-15 | available (planning state, not confirmed) _Evidence: N-QUOTE-Q-009_ |
| Q-010 | QuietWorks | accessibility | quiet room staffing | TWD 18,000 | 20 | 2026-10-17 | 2026-09-10 | available (planning state, not confirmed) _Evidence: N-QUOTE-Q-010_ |
| Q-004 | City Pantry | catering | lunch and two breaks | TWD 126,000 | 300 | 2026-10-17 | 2026-09-12 | available (planning state, not confirmed) _Evidence: N-QUOTE-Q-004_ |

## 7. Accessibility and safety evidence and limits

**Hard accessibility provisions (cannot be traded away):**

| Provision | `OPT-2026-10-17-Q-003` | `OPT-2026-10-17-Q-004` |
|---|---|---|
| hearing loop | pass: Hearing loop provided by ['Q-006']. _Evidence: CHK-OPT-2026-10-17-Q-003-access-hearing_loop_ | pass: Hearing loop provided by ['Q-006']. _Evidence: CHK-OPT-2026-10-17-Q-004-access-hearing_loop_ |
| step free access | pass: step_free_access: stated by the venue coordination record (case record) and located on the official floor plan (4 spatial observation(s)). The plan does not prove ["today's elevator operation", 'unobstructed route', 'seating configuration', 'acoustic performance']. _Evidence: CHK-OPT-2026-10-17-Q-003-access-step_free_access_ | pass: step_free_access: stated by the venue coordination record (case record) and located on the official floor plan (4 spatial observation(s)). The plan does not prove ["today's elevator operation", 'unobstructed route', 'seating configuration', 'acoustic performance']. _Evidence: CHK-OPT-2026-10-17-Q-004-access-step_free_access_ |
| wheelchair seating | pass: wheelchair_seating: stated by the venue coordination record (case record) and located on the official floor plan (1 spatial observation(s)). The plan does not prove ["today's elevator operation", 'unobstructed route', 'seating configuration', 'acoustic performance']. _Evidence: CHK-OPT-2026-10-17-Q-003-access-wheelchair_seating_ | pass: wheelchair_seating: stated by the venue coordination record (case record) and located on the official floor plan (1 spatial observation(s)). The plan does not prove ["today's elevator operation", 'unobstructed route', 'seating configuration', 'acoustic performance']. _Evidence: CHK-OPT-2026-10-17-Q-004-access-wheelchair_seating_ |
| live captions | pass: Live captions provided by ['Q-005']. _Evidence: CHK-OPT-2026-10-17-Q-003-access-live_captions_ | pass: Live captions provided by ['Q-005']. _Evidence: CHK-OPT-2026-10-17-Q-004-access-live_captions_ |
| staffed quiet room | pass: Staffed quiet room: V.I.P. Room in the venue package, staffed by ['Q-010']. _Evidence: CHK-OPT-2026-10-17-Q-003-access-staffed_quiet_room_ | pass: Staffed quiet room: V.I.P. Room in the venue package, staffed by ['Q-010']. _Evidence: CHK-OPT-2026-10-17-Q-004-access-staffed_quiet_room_ |

_Evidence: B-accessibility-requirements, STK-I2-L77_

**Official 4F floor plan — spatial observations (spatial evidence only):**

- Legend defines separate symbols for Disabled Wheelchair Area (blue), Restroom for the Disabled (magenta), Accessible Elevator (magenta wheelchair over an elevator cross), Drinking Fountain for the Disabled, Charging Socket, AED, and two kinds of emergency exit. — page 1, x 0.06–0.20, y 0.12–0.71 (fractions of page from top-left) _Evidence: N-FP-FP-legend_
- The Plenary Hall seating and the Plenary Hall Stage are on 4F, with the stage on the east side of the seating. — page 1, x 0.58–0.88, y 0.23–0.64 (fractions of page from top-left) _Evidence: N-FP-FP-plenary-hall_
- Four Disabled Wheelchair Area symbols are drawn inside the Plenary Hall seating: two in the north seating section and two in the south seating section. The symbols mark locations only; they do not state how many wheelchair spaces exist. — page 1, x 0.70–0.79, y 0.29–0.59 (fractions of page from top-left) _Evidence: N-FP-FP-hall-wheelchair-areas_
- The V.I.P. Room (貴賓廳) is on the same floor, in the west wing, separated from the Plenary Hall by the central core (Room 401, corridors, restrooms and service rooms). — page 1, x 0.29–0.42, y 0.40–0.68 (fractions of page from top-left) _Evidence: N-FP-FP-vip-room_
- Room 401 Meeting Room lies west of the Plenary Hall seating, separated from it by restrooms 410–415, VIP lounges, an office, a control room and a storage room. — page 1, x 0.44–0.53, y 0.32–0.54 (fractions of page from top-left) _Evidence: N-FP-FP-room-401_
- Accessible Elevator symbols mark elevators EV1/EV2 and EV3/EV4 in the south lobby, labelled 'Accessible Elevator' and 'Elevator'. — page 1, x 0.58–0.71, y 0.69–0.74 (fractions of page from top-left) _Evidence: N-FP-FP-accessible-elevators-south_
- An Accessible Elevator symbol marks EV9 at the south-east corner of the Plenary Hall; the label 'Accessible Elevator' appears between EV9 and EV11. — page 1, x 0.79–0.83, y 0.59–0.66 (fractions of page from top-left) _Evidence: N-FP-FP-accessible-elevator-ev9_
- A Restroom for the Disabled symbol is drawn between restrooms 407 and 408 in the south-west, next to a Drinking Fountain for the Disabled, a Baby Changing symbol and an AED. — page 1, x 0.48–0.52, y 0.74–0.80 (fractions of page from top-left) _Evidence: N-FP-FP-accessible-restroom-south_
- An Accessible Elevator symbol (magenta wheelchair over an elevator cross, as in the legend) marks EV13 in the north-west EV13/EV14 elevator bank; the adjacent EV14 shows the plain Elevator symbol. — page 1, x 0.35–0.38, y 0.32–0.36 (fractions of page from top-left) _Evidence: N-FP-FP-accessible-elevator-ev13_
- Emergency exit symbols mark stairs A, B, C, D, F, G and H around the floor; red symbols mean exit to 1F outdoors and rooftop, blue symbols mean exit to the 1F lobby and rooftop. — page 1, x 0.40–0.88, y 0.08–0.80 (fractions of page from top-left) _Evidence: N-FP-FP-emergency-exits_
- Title block: TICC '4F Floor Plan', dated 105年11月8日 (ROC calendar, 8 November 2016). Note 1 says dimensions and layout are drawn from the original architectural drawings and are for reference only; note 2 says vendors must measure on site. — page 1, x 0.92–0.99, y 0.55–0.99 (fractions of page from top-left) _Evidence: N-FP-FP-title-block_

- **Limits:** the floor plan does not prove today's elevator operation, unobstructed route, seating configuration, acoustic performance; counts and hearing-loop availability come from the venue coordination record (a case record). _Evidence: N-BRIEF-floor_plan_does_not_prove, STK-I3-L193_
- **Official venue rule (source fact):** Venue rule 9 (livestream): 9.本中心自111年起活動若有直播需求，請主動告知承辦人，恕不開放非本中心合約廠商提供服務。 _Evidence: N-VENUE-official_rule_livestream_contract_vendors_only_
- **Official venue rule (source fact):** Venue rule 10 (technical coordination and safety briefing): 10.凡租用大會堂之客戶需於活動前出席技術協調會及安全逃生講習，詳情請洽承辦人。 _Evidence: N-VENUE-official_rule_technical_and_safety_briefing_

**Dietary and safety:**

- `OPT-2026-10-17-Q-003`: pass — Documented dietary needs are covered by the Operations-coordinated response for ['Q-003'] (case record); severe-allergy contacts are a separate open prerequisite. _Evidence: CHK-OPT-2026-10-17-Q-003-dietary_
- `OPT-2026-10-17-Q-004`: pass — Documented dietary needs are covered by the Operations-coordinated response for ['Q-004'] (case record); severe-allergy contacts are a separate open prerequisite. _Evidence: CHK-OPT-2026-10-17-Q-004-dietary_
- Severe-allergy follow-up: 4 request(s), aggregate only. Named contacts are held by Operations and are not reproduced here. _Evidence: B-need-severe_allergy_follow_up, N-BRIEF-named_contacts_holder, ASG-PRIVACY_

## 8. Recommendation or deferral

**Outcome: `deferred-to-operations`.** No option is recommended. The choice is deferred to Operations. _Evidence: DEC-recommendation_

**Question for Operations:** Operations judgment required: choose between lower cost and greater budget headroom (OPT-2026-10-17-Q-003) and the larger catering capacity buffer (OPT-2026-10-17-Q-004).

Rationale: No candidate dominates on the evidenced factors, and the stakeholder gave no fixed ordering of these tradeoffs; the choice is left to Operations.

Factors (no weights, no ranking; a preference is stated only when one option dominates):

| Factor | Direction | `OPT-2026-10-17-Q-003` | `OPT-2026-10-17-Q-004` |
|---|---|---|---|
| lower cost and greater budget headroom | lower total is better | 494000 | 512000 _Evidence: TO-cost_ |
| the larger catering capacity buffer | larger buffer is better | 15 | 55 _Evidence: TO-catering_buffer_ |
| fewer open condition types | fewer normalized condition types is better | 8 | 8 _Evidence: TO-open_conditions_ |
| fewer unverified checks | fewer is better | 0 | 0 _Evidence: TO-unverified_checks_ |
| all quotes valid through the decision deadline | all valid is better than not all valid | True | True _Evidence: TO-quote_validity_ |

Stakeholder context (informs the tradeoff; not a weight): CTX-STK-I2-L65, CTX-STK-I1-L111, CTX-STK-I3-L85, CTX-STK-I3-L97, CTX-STK-I3-L121, CTX-walk-in-forecast. _Evidence: CTX-STK-I2-L65, CTX-STK-I1-L111, CTX-STK-I3-L85, CTX-STK-I3-L97, CTX-STK-I3-L121, CTX-walk-in-forecast_
Vendor experience: Vendor experience / familiar-supplier status is not evidenced by any disclosed source; it is noted qualitatively and not scored. _Evidence: NOTE-vendor-experience_

Excluded from recommendation:

- `OPT-2026-10-17-Q-003-sub-Q-007` (infeasible) _Evidence: OPT-2026-10-17-Q-003-sub-Q-007_
- `OPT-2026-10-17-Q-003-add-Q-008` (infeasible) _Evidence: OPT-2026-10-17-Q-003-add-Q-008_
- `OPT-2026-10-17-Q-004-sub-Q-007` (infeasible) _Evidence: OPT-2026-10-17-Q-004-sub-Q-007_
- `OPT-2026-10-17-Q-004-add-Q-008` (infeasible) _Evidence: OPT-2026-10-17-Q-004-add-Q-008_
- `OPT-2026-10-24-fallback` (infeasible) _Evidence: OPT-2026-10-24-fallback_

## 9. Feasible-option shortfall

The brief asks for 2 feasible options; 0 are feasible on current evidence. No option is upgraded and none is fabricated. Owner: Operations. _Evidence: UNR-feasible-option-shortfall, N-BRIEF-requested_feasible_options, N-BRIEF-no_fabricated_second_option, N-BRIEF-conditional_not_feasible_rule, ASG-NO-INVENT_

## 10. Risks

- Venue hold expires 2026-09-05; decision deadline 2026-09-04 (hold outlasts the deadline). A hold is not a confirmation. _Evidence: X-hold-vs-deadline_
- The walk-in forecast (35) has medium confidence; a smaller catering buffer may need earlier refreshing if registrations increase. _Evidence: N-ATT-group-walk_ins, STK-I2-L65_

Capacity margins of the conditional options, as recorded by the Phase 3 checks (a margin of 0 leaves no room for an additional request):

- `OPT-2026-10-17-Q-003` capacity margin — Audience places: capacity 500 for 245 (margin 255). _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-venue_
- `OPT-2026-10-17-Q-003` capacity margin — Catering Q-003 for all groups incl. staff and speakers: capacity 260 for 245 (margin 15). The register states the capacity number only; who it covers is not further specified. _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-catering-Q-003_
- `OPT-2026-10-17-Q-003` capacity margin — Quiet room (room occupancy and staffing): capacity 20 for 9 (margin 11). _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-quiet-room_
- `OPT-2026-10-17-Q-003` capacity margin — Wheelchair spaces: capacity 6 for 6 (margin 0). Companions use ordinary places. _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-wheelchair_
- `OPT-2026-10-17-Q-003` capacity margin — Live captions: capacity 500 for 23 (margin 477). _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-live_captions_
- `OPT-2026-10-17-Q-003` capacity margin — Hearing loop: capacity 500 for 7 (margin 493). _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-hearing_loop_
- `OPT-2026-10-17-Q-003` capacity margin — Security coverage: capacity 500 for 245 (margin 255). _Evidence: CHK-OPT-2026-10-17-Q-003-capacity-security_
- `OPT-2026-10-17-Q-004` capacity margin — Audience places: capacity 500 for 245 (margin 255). _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-venue_
- `OPT-2026-10-17-Q-004` capacity margin — Catering Q-004 for all groups incl. staff and speakers: capacity 300 for 245 (margin 55). The register states the capacity number only; who it covers is not further specified. _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-catering-Q-004_
- `OPT-2026-10-17-Q-004` capacity margin — Quiet room (room occupancy and staffing): capacity 20 for 9 (margin 11). _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-quiet-room_
- `OPT-2026-10-17-Q-004` capacity margin — Wheelchair spaces: capacity 6 for 6 (margin 0). Companions use ordinary places. _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-wheelchair_
- `OPT-2026-10-17-Q-004` capacity margin — Live captions: capacity 500 for 23 (margin 477). _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-live_captions_
- `OPT-2026-10-17-Q-004` capacity margin — Hearing loop: capacity 500 for 7 (margin 493). _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-hearing_loop_
- `OPT-2026-10-17-Q-004` capacity margin — Security coverage: capacity 500 for 245 (margin 255). _Evidence: CHK-OPT-2026-10-17-Q-004-capacity-security_

## 11. Unknowns and unresolved items

- `UNR-feasible-option-shortfall`: The brief asks for 2 feasible options; 0 are feasible on current evidence. No option is upgraded and none is fabricated. (owner Operations) _Evidence: UNR-feasible-option-shortfall_
- Vendor experience / familiar-supplier status is not evidenced by any disclosed source; it is noted qualitatively and not scored. _Evidence: NOTE-vendor-experience_

## 12. Change impacts

If a source changes, these parts of the package must be reconsidered (derived from the evidence links, not assumed):

| Source | Claims | Options | Deliverable sections |
|---|---|---|---|
| `SRC-BRIEF` | 89 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | event-plan §3 headcount, event-plan §4 timing and run of show, event-calendar.ics, event-plan §5 budget, event-plan §7 accessibility, vendor-comparison.csv, event-plan §6 options, draft-communications.md, event-plan §8 recommendation, event-plan §13 approvals |
| `SRC-CALENDAR` | 37 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | event-plan §4 timing and run of show, event-calendar.ics, vendor-comparison.csv, event-plan §6 options, draft-communications.md, event-plan §8 recommendation |
| `SRC-BUDGET` | 8 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | event-plan §5 budget, vendor-comparison.csv, event-plan §6 options, draft-communications.md, event-plan §8 recommendation, event-plan §13 approvals |
| `SRC-ATTENDEE` | 16 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | event-plan §3 headcount, vendor-comparison.csv, event-plan §6 options, draft-communications.md, event-plan §8 recommendation |
| `SRC-VENDOR` | 34 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | vendor-comparison.csv, event-plan §6 options, draft-communications.md, event-plan §8 recommendation, event-plan §13 approvals, event-plan §5 budget, event-plan §7 accessibility |
| `SRC-TICC-HALL` | 9 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | vendor-comparison.csv, event-plan §6 options, draft-communications.md, event-plan §8 recommendation |
| `SRC-TICC-ACCESS` | 1 | none | none |
| `SRC-TICC-4F` | 11 | OPT-2026-10-17-Q-003, OPT-2026-10-17-Q-003-add-Q-008, OPT-2026-10-17-Q-003-sub-Q-007, OPT-2026-10-17-Q-004, OPT-2026-10-17-Q-004-add-Q-008, OPT-2026-10-17-Q-004-sub-Q-007, OPT-2026-10-24-fallback | event-plan §7 accessibility, vendor-comparison.csv, event-plan §6 options, draft-communications.md |

_Evidence: SRC-BRIEF, SRC-CALENDAR, SRC-BUDGET, SRC-ATTENDEE, SRC-VENDOR, SRC-TICC-HALL, SRC-TICC-ACCESS, SRC-TICC-4F_

## 13. Owners, approvals and review requests

| Approval | Owner | Status | Option |
|---|---|---|---|
| Operations approval of plan, date 2026-10-17 and venue | Operations | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-operations-plan_ |
| Ordinary approval of accessibility spending TWD 60000 by Learner Experience | Learner Experience | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-accessibility_ |
| Ordinary approval of catering spending TWD 108000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-catering_ |
| Ordinary approval of communications spending TWD 25000 by Communications | Communications | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-communications_ |
| Ordinary approval of contingency spending TWD 40000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-contingency_ |
| Ordinary approval of production spending TWD 78000 by Programme | Programme | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-production_ |
| Ordinary approval of security spending TWD 28000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-security_ |
| Ordinary approval of venue spending TWD 155000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-003` _Evidence: APR-OPT-2026-10-17-Q-003-budget-venue_ |
| Operations approval of plan, date 2026-10-17 and venue | Operations | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-operations-plan_ |
| Ordinary approval of accessibility spending TWD 60000 by Learner Experience | Learner Experience | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-accessibility_ |
| Ordinary approval of catering spending TWD 126000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-catering_ |
| Ordinary approval of communications spending TWD 25000 by Communications | Communications | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-communications_ |
| Ordinary approval of contingency spending TWD 40000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-contingency_ |
| Ordinary approval of production spending TWD 78000 by Programme | Programme | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-production_ |
| Ordinary approval of security spending TWD 28000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-security_ |
| Ordinary approval of venue spending TWD 155000 by Operations | Operations | **pending** | `OPT-2026-10-17-Q-004` _Evidence: APR-OPT-2026-10-17-Q-004-budget-venue_ |

Approvals for infeasible options are recorded in the decision model but are not requested.

**Review requests:** see `draft-communications.md` (all messages are unsent drafts).

## Appendix: Evidence index

| ID | Resolves to |
|---|---|
| `APR-OPT-2026-10-17-Q-003-budget-accessibility` | Phase 3 approval (pending): Ordinary approval of accessibility spending TWD 60000 by Learner Experience |
| `APR-OPT-2026-10-17-Q-003-budget-catering` | Phase 3 approval (pending): Ordinary approval of catering spending TWD 108000 by Operations |
| `APR-OPT-2026-10-17-Q-003-budget-communications` | Phase 3 approval (pending): Ordinary approval of communications spending TWD 25000 by Communications |
| `APR-OPT-2026-10-17-Q-003-budget-contingency` | Phase 3 approval (pending): Ordinary approval of contingency spending TWD 40000 by Operations |
| `APR-OPT-2026-10-17-Q-003-budget-production` | Phase 3 approval (pending): Ordinary approval of production spending TWD 78000 by Programme |
| `APR-OPT-2026-10-17-Q-003-budget-security` | Phase 3 approval (pending): Ordinary approval of security spending TWD 28000 by Operations |
| `APR-OPT-2026-10-17-Q-003-budget-venue` | Phase 3 approval (pending): Ordinary approval of venue spending TWD 155000 by Operations |
| `APR-OPT-2026-10-17-Q-003-operations-plan` | Phase 3 approval (pending): Operations approval of plan, date 2026-10-17 and venue |
| `APR-OPT-2026-10-17-Q-004-budget-accessibility` | Phase 3 approval (pending): Ordinary approval of accessibility spending TWD 60000 by Learner Experience |
| `APR-OPT-2026-10-17-Q-004-budget-catering` | Phase 3 approval (pending): Ordinary approval of catering spending TWD 126000 by Operations |
| `APR-OPT-2026-10-17-Q-004-budget-communications` | Phase 3 approval (pending): Ordinary approval of communications spending TWD 25000 by Communications |
| `APR-OPT-2026-10-17-Q-004-budget-contingency` | Phase 3 approval (pending): Ordinary approval of contingency spending TWD 40000 by Operations |
| `APR-OPT-2026-10-17-Q-004-budget-production` | Phase 3 approval (pending): Ordinary approval of production spending TWD 78000 by Programme |
| `APR-OPT-2026-10-17-Q-004-budget-security` | Phase 3 approval (pending): Ordinary approval of security spending TWD 28000 by Operations |
| `APR-OPT-2026-10-17-Q-004-budget-venue` | Phase 3 approval (pending): Ordinary approval of venue spending TWD 155000 by Operations |
| `APR-OPT-2026-10-17-Q-004-operations-plan` | Phase 3 approval (pending): Operations approval of plan, date 2026-10-17 and venue |
| `ASG-CHANGED-INPUTS` | Assignment (Changed inputs and recovery): "Hold missing fields, ambiguous/duplicate identities, incompatible meanings or invalid required values before dependent interpretation; do no" |
| `ASG-CLOCK` | Assignment (Scenario): "The exercise's business clock is 26 August 2026, 12:00, Asia/Taipei; record actual source retrieval times separately." |
| `ASG-NO-INVENT` | Assignment (Incomplete results): "Do not invent options, facts or approvals to obtain a normal result." |
| `ASG-PRIVACY` | Assignment (Your task): "Do not copy private attendee medical/contact details into general artifacts." |
| `B-accessibility-requirements` | Phase 3 baseline: Hard accessibility provisions (cannot be traded away): [{'key': 'hearing_loop', 'basis': ['STK-I2-L77']}, {'key': 'step_free_access', 'basis': ['N-BRIEF-hard_re |
| `B-allowances` | Phase 3 baseline: Budget allowances counted in the ceiling: {'communications': 25000, 'contingency': 40000} |
| `B-budget-accessibility` | Phase 3 baseline: Budget accessibility: {'category': 'accessibility', 'planned_amount_twd': 65000, 'approval_limit_twd': 80000, 'committed_amount_twd': 0, 'owner': 'Learner Exper |
| `B-budget-catering` | Phase 3 baseline: Budget catering: {'category': 'catering', 'planned_amount_twd': 115000, 'approval_limit_twd': 135000, 'committed_amount_twd': 0, 'owner': 'Operations'} |
| `B-budget-communications` | Phase 3 baseline: Budget communications: {'category': 'communications', 'planned_amount_twd': 25000, 'approval_limit_twd': 30000, 'committed_amount_twd': 0, 'owner': 'Communicati |
| `B-budget-contingency` | Phase 3 baseline: Budget contingency: {'category': 'contingency', 'planned_amount_twd': 40000, 'approval_limit_twd': 50000, 'committed_amount_twd': 0, 'owner': 'Operations'} |
| `B-budget-production` | Phase 3 baseline: Budget production: {'category': 'production', 'planned_amount_twd': 85000, 'approval_limit_twd': 100000, 'committed_amount_twd': 0, 'owner': 'Programme'} |
| `B-budget-security` | Phase 3 baseline: Budget security: {'category': 'security', 'planned_amount_twd': 25000, 'approval_limit_twd': 35000, 'committed_amount_twd': 0, 'owner': 'Operations'} |
| `B-budget-venue` | Phase 3 baseline: Budget venue: {'category': 'venue', 'planned_amount_twd': 155000, 'approval_limit_twd': 180000, 'committed_amount_twd': 0, 'owner': 'Operations'} |
| `B-ceiling` | Phase 3 baseline: Planning ceiling TWD: 520000 |
| `B-decision-deadline` | Phase 3 baseline: Plan and budget decision deadline: 2026-09-04T17:00:00+08:00 |
| `B-event-window` | Phase 3 baseline: Preferred event window: {'date': '2026-10-17', 'start': '2026-10-17T09:30:00+08:00', 'end': '2026-10-17T17:00:00+08:00', 'priority': 'hard'} |
| `B-fallback-window` | Phase 3 baseline: Fallback event window: {'date': '2026-10-24', 'start': '2026-10-24T09:30:00+08:00', 'end': '2026-10-24T17:00:00+08:00', 'priority': 'soft'} |
| `B-headcount` | Phase 3 baseline: Planning headcount: {'total': 245, 'groups': {'fellows': 148, 'partners': 32, 'staff': 18, 'speakers': 12, 'walk_ins': 35}, 'basis': 'sum of separate groups; ov |
| `B-keynote` | Phase 3 baseline: Keynote availability: {'date': '2026-10-17', 'start': '2026-10-17T10:00:00+08:00', 'end': '2026-10-17T11:00:00+08:00', 'priority': 'hard', 'owner': 'Programme'} |
| `B-need-halal_meal` | Phase 3 baseline: Need halal_meal (overlapping): 12 |
| `B-need-hearing_loop` | Phase 3 baseline: Need hearing_loop (overlapping): 7 |
| `B-need-live_captions` | Phase 3 baseline: Need live_captions (overlapping): 23 |
| `B-need-mobility_companion` | Phase 3 baseline: Need mobility_companion (overlapping): 4 |
| `B-need-quiet_room` | Phase 3 baseline: Need quiet_room (overlapping): 9 |
| `B-need-severe_allergy_follow_up` | Phase 3 baseline: Need severe_allergy_follow_up (overlapping): 4 |
| `B-need-vegetarian_meal` | Phase 3 baseline: Need vegetarian_meal (overlapping): 28 |
| `B-need-wheelchair_seating` | Phase 3 baseline: Need wheelchair_seating (overlapping): 6 |
| `B-programme` | Phase 3 baseline: Programme inputs: {'demo_count': 12, 'roster': ['DEMO-01', 'DEMO-02', 'DEMO-03', 'DEMO-04', 'DEMO-05', 'DEMO-06', 'DEMO-07', 'DEMO-08', 'DEMO-09', 'DEMO-10', 'D |
| `B-teardown` | Phase 3 baseline: Teardown window: {'start': '2026-10-17T17:00:00+08:00', 'end': '2026-10-17T18:30:00+08:00', 'priority': 'hard'} |
| `B-venue-hold` | Phase 3 baseline: Venue hold window (a hold is not a confirmation): {'date': '2026-10-17', 'start': '2026-10-17T07:30:00+08:00', 'end': '2026-10-17T18:30:00+08:00', 'priority': ' |
| `CHK-OPT-2026-10-17-Q-003-access-hearing_loop` | Phase 3 check: Hearing loop provided by ['Q-006']. |
| `CHK-OPT-2026-10-17-Q-003-access-live_captions` | Phase 3 check: Live captions provided by ['Q-005']. |
| `CHK-OPT-2026-10-17-Q-003-access-staffed_quiet_room` | Phase 3 check: Staffed quiet room: V.I.P. Room in the venue package, staffed by ['Q-010']. |
| `CHK-OPT-2026-10-17-Q-003-access-step_free_access` | Phase 3 check: step_free_access: stated by the venue coordination record (case record) and located on the official floor plan (4 spatial observation(s)). The plan does not pro |
| `CHK-OPT-2026-10-17-Q-003-access-wheelchair_seating` | Phase 3 check: wheelchair_seating: stated by the venue coordination record (case record) and located on the official floor plan (1 spatial observation(s)). The plan does not p |
| `CHK-OPT-2026-10-17-Q-003-budget-accessibility` | Phase 3 check: accessibility: 60000 within approval limit 80000 (variance from planned 65000: -5000); ordinary approval by Learner Experience still pending. |
| `CHK-OPT-2026-10-17-Q-003-budget-catering` | Phase 3 check: catering: 108000 within approval limit 135000 (variance from planned 115000: -7000); ordinary approval by Operations still pending. |
| `CHK-OPT-2026-10-17-Q-003-budget-ceiling` | Phase 3 check: Total 494000 including allowances is within the ceiling 520000 (remaining 26000). |
| `CHK-OPT-2026-10-17-Q-003-budget-production` | Phase 3 check: production: 78000 within approval limit 100000 (variance from planned 85000: -7000); ordinary approval by Programme still pending. |
| `CHK-OPT-2026-10-17-Q-003-budget-security` | Phase 3 check: security: 28000 within approval limit 35000 (variance from planned 25000: +3000); ordinary approval by Operations still pending. |
| `CHK-OPT-2026-10-17-Q-003-budget-venue` | Phase 3 check: venue: 155000 within approval limit 180000 (equal to planned); ordinary approval by Operations still pending. |
| `CHK-OPT-2026-10-17-Q-003-capacity-catering-Q-003` | Phase 3 check: Catering Q-003 for all groups incl. staff and speakers: capacity 260 for 245 (margin 15). The register states the capacity number only; who it covers is not fur |
| `CHK-OPT-2026-10-17-Q-003-capacity-hearing_loop` | Phase 3 check: Hearing loop: capacity 500 for 7 (margin 493). |
| `CHK-OPT-2026-10-17-Q-003-capacity-live_captions` | Phase 3 check: Live captions: capacity 500 for 23 (margin 477). |
| `CHK-OPT-2026-10-17-Q-003-capacity-quiet-room` | Phase 3 check: Quiet room (room occupancy and staffing): capacity 20 for 9 (margin 11). |
| `CHK-OPT-2026-10-17-Q-003-capacity-security` | Phase 3 check: Security coverage: capacity 500 for 245 (margin 255). |
| `CHK-OPT-2026-10-17-Q-003-capacity-venue` | Phase 3 check: Audience places: capacity 500 for 245 (margin 255). |
| `CHK-OPT-2026-10-17-Q-003-capacity-wheelchair` | Phase 3 check: Wheelchair spaces: capacity 6 for 6 (margin 0). Companions use ordinary places. |
| `CHK-OPT-2026-10-17-Q-003-dietary` | Phase 3 check: Documented dietary needs are covered by the Operations-coordinated response for ['Q-003'] (case record); severe-allergy contacts are a separate open prerequisit |
| `CHK-OPT-2026-10-17-Q-004-access-hearing_loop` | Phase 3 check: Hearing loop provided by ['Q-006']. |
| `CHK-OPT-2026-10-17-Q-004-access-live_captions` | Phase 3 check: Live captions provided by ['Q-005']. |
| `CHK-OPT-2026-10-17-Q-004-access-staffed_quiet_room` | Phase 3 check: Staffed quiet room: V.I.P. Room in the venue package, staffed by ['Q-010']. |
| `CHK-OPT-2026-10-17-Q-004-access-step_free_access` | Phase 3 check: step_free_access: stated by the venue coordination record (case record) and located on the official floor plan (4 spatial observation(s)). The plan does not pro |
| `CHK-OPT-2026-10-17-Q-004-access-wheelchair_seating` | Phase 3 check: wheelchair_seating: stated by the venue coordination record (case record) and located on the official floor plan (1 spatial observation(s)). The plan does not p |
| `CHK-OPT-2026-10-17-Q-004-budget-accessibility` | Phase 3 check: accessibility: 60000 within approval limit 80000 (variance from planned 65000: -5000); ordinary approval by Learner Experience still pending. |
| `CHK-OPT-2026-10-17-Q-004-budget-catering` | Phase 3 check: catering: 126000 within approval limit 135000 (variance from planned 115000: +11000); ordinary approval by Operations still pending. |
| `CHK-OPT-2026-10-17-Q-004-budget-ceiling` | Phase 3 check: Total 512000 including allowances is within the ceiling 520000 (remaining 8000). |
| `CHK-OPT-2026-10-17-Q-004-budget-production` | Phase 3 check: production: 78000 within approval limit 100000 (variance from planned 85000: -7000); ordinary approval by Programme still pending. |
| `CHK-OPT-2026-10-17-Q-004-budget-security` | Phase 3 check: security: 28000 within approval limit 35000 (variance from planned 25000: +3000); ordinary approval by Operations still pending. |
| `CHK-OPT-2026-10-17-Q-004-budget-venue` | Phase 3 check: venue: 155000 within approval limit 180000 (equal to planned); ordinary approval by Operations still pending. |
| `CHK-OPT-2026-10-17-Q-004-capacity-catering-Q-004` | Phase 3 check: Catering Q-004 for all groups incl. staff and speakers: capacity 300 for 245 (margin 55). The register states the capacity number only; who it covers is not fur |
| `CHK-OPT-2026-10-17-Q-004-capacity-hearing_loop` | Phase 3 check: Hearing loop: capacity 500 for 7 (margin 493). |
| `CHK-OPT-2026-10-17-Q-004-capacity-live_captions` | Phase 3 check: Live captions: capacity 500 for 23 (margin 477). |
| `CHK-OPT-2026-10-17-Q-004-capacity-quiet-room` | Phase 3 check: Quiet room (room occupancy and staffing): capacity 20 for 9 (margin 11). |
| `CHK-OPT-2026-10-17-Q-004-capacity-security` | Phase 3 check: Security coverage: capacity 500 for 245 (margin 255). |
| `CHK-OPT-2026-10-17-Q-004-capacity-venue` | Phase 3 check: Audience places: capacity 500 for 245 (margin 255). |
| `CHK-OPT-2026-10-17-Q-004-capacity-wheelchair` | Phase 3 check: Wheelchair spaces: capacity 6 for 6 (margin 0). Companions use ordinary places. |
| `CHK-OPT-2026-10-17-Q-004-dietary` | Phase 3 check: Documented dietary needs are covered by the Operations-coordinated response for ['Q-004'] (case record); severe-allergy contacts are a separate open prerequisit |
| `CTX-STK-I1-L111` | Phase 4 stakeholder context: Stakeholder context STK-I1-L111; informs the tradeoff statement, not a weight. |
| `CTX-STK-I2-L65` | Phase 4 stakeholder context: Stakeholder context STK-I2-L65; informs the tradeoff statement, not a weight. |
| `CTX-STK-I3-L121` | Phase 4 stakeholder context: Stakeholder context STK-I3-L121; informs the tradeoff statement, not a weight. |
| `CTX-STK-I3-L85` | Phase 4 stakeholder context: Stakeholder context STK-I3-L85; informs the tradeoff statement, not a weight. |
| `CTX-STK-I3-L97` | Phase 4 stakeholder context: Stakeholder context STK-I3-L97; informs the tradeoff statement, not a weight. |
| `CTX-walk-in-forecast` | Phase 4 stakeholder context: Walk-in forecast 35 people at medium confidence; relevant to the catering buffer tradeoff (STK-I2-L65). |
| `DEC-recommendation` | Phase 4 decision record: Recommendation outcome: deferred-to-operations |
| `DEP-P-accessibility-walkthrough` | Phase 3 dependency: Accessibility walkthrough: required condition with no evidence of completion. Depends on ['P-venue-confirmation']. |
| `DEP-P-livestream-network-test-Q-008` | Phase 3 dependency: Livestream network test for Q-008: required condition with no evidence of completion. |
| `DEP-P-livestream-venue-confirmation-Q-008` | Phase 3 dependency: Venue confirmation for livestream Q-008: required condition with no evidence of completion. |
| `DEP-P-severe-allergy-contacts` | Phase 3 dependency: Severe-allergy contact coordination: required condition with no evidence of completion. |
| `DEP-P-ticc-technical-safety-briefing` | Phase 3 dependency: TICC technical coordination meeting and safety evacuation briefing: required condition with no evidence of completion. |
| `DEP-P-venue-confirmation` | Phase 3 dependency: Venue confirmation: required condition with no evidence of completion. |
| `DEP-Q-003-confirmation` | Phase 3 dependency: Q-003 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-Q-004-confirmation` | Phase 3 dependency: Q-004 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-Q-005-confirmation` | Phase 3 dependency: Q-005 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-Q-006-confirmation` | Phase 3 dependency: Q-006 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-Q-007-confirmation` | Phase 3 dependency: Q-007 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-Q-008-confirmation` | Phase 3 dependency: Q-008 is 'conditional': an outstanding required condition must be resolved. |
| `DEP-Q-009-confirmation` | Phase 3 dependency: Q-009 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-Q-010-confirmation` | Phase 3 dependency: Q-010 is 'available', a planning state, not a confirmed booking; explicit confirmation is required before the option can be feasible. |
| `DEP-access-hearing_loop` | Phase 3 dependency: No quote in this option provides hearing loop. |
| `DEP-access-live_captions` | Phase 3 dependency: No quote in this option provides live captions. |
| `DEP-access-staffed_quiet_room` | Phase 3 dependency: No quiet-room staffing in this option. |
| `DEP-budget-ceiling` | Phase 3 dependency: Total cost cannot be stated: no quotes for ['accessibility', 'catering', 'production', 'security'] on 2026-10-24. |
| `DEP-budget-production` | Phase 3 dependency: production: 133000 exceeds approval limit 100000 (variance from planned 85000: +48000); explicit approval by Programme required. |
| `DEP-readiness` | Phase 3 dependency: Readiness by 09:30 and clearance by 18:30 is not confirmed for ['Q-007']; no vendor durations are given, so it cannot be derived. |
| `DEP-service-accessibility` | Phase 3 dependency: No accessibility quote is available on 2026-10-24; availability cannot be assumed. |
| `DEP-service-catering` | Phase 3 dependency: No catering quote is available on 2026-10-24; availability cannot be assumed. |
| `DEP-service-production` | Phase 3 dependency: No production quote is available on 2026-10-24; availability cannot be assumed. |
| `DEP-service-security` | Phase 3 dependency: No security quote is available on 2026-10-24; availability cannot be assumed. |
| `N-ATT-group-walk_ins` | Claim (attendee-group, supported): SRC-ATTENDEE 'Attendee Signals'!A6:H6 (retrieved 2026-10-07T21:20:23.806Z) |
| `N-BRIEF-checkin_target_percent` | Claim (brief-fact, supported): SRC-BRIEF Event brief ¶5 [block e6940ea5-d391-47cb-b64c-196387d979fc] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-conditional_not_feasible_rule` | Claim (brief-fact, supported): SRC-BRIEF Exercise source clarification — authored 12 September 2026 ¶1 [block 5eb74389-3826-4942-83bb-41e6bad56dd6] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-event_name` | Claim (brief-fact, supported): SRC-BRIEF Event brief ¶2 [block 298c39a7-ff6a-49a9-a259-bfbc100124b1] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-floor_plan_does_not_prove` | Claim (brief-fact, supported): SRC-BRIEF Venue coordination record ¶4 [block 8f25fe93-a57e-441f-be1b-f1875290301f] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-named_contacts_holder` | Claim (brief-fact, supported): SRC-BRIEF Venue coordination record ¶5 [block 2fdefb04-6881-4c55-8302-3822705b5a45] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-no_fabricated_second_option` | Claim (brief-fact, supported): SRC-BRIEF Exercise source clarification — authored 12 September 2026 ¶1 [block 5eb74389-3826-4942-83bb-41e6bad56dd6] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-planner_schedule_choices` | Claim (brief-fact, supported): SRC-BRIEF Exercise programme confirmation — authored 12 September 2026 ¶3 [block 3af34366-805b-42d8-a40a-e1a7d56ee103] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-requested_feasible_options` | Claim (brief-fact, supported): SRC-BRIEF Event brief ¶3 [block 4aa2f6dc-3460-435b-8649-99a67d325798] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-roster_change_owner` | Claim (brief-fact, supported): SRC-BRIEF Exercise programme confirmation — authored 12 September 2026 ¶3 [block 3af34366-805b-42d8-a40a-e1a7d56ee103] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-success_accessibility_response_before_event` | Claim (brief-fact, supported): SRC-BRIEF Event brief ¶5 [block e6940ea5-d391-47cb-b64c-196387d979fc] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-success_all_demos_run` | Claim (brief-fact, supported): SRC-BRIEF Event brief ¶5 [block e6940ea5-d391-47cb-b64c-196387d979fc] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-BRIEF-venue_name` | Claim (brief-fact, supported): SRC-BRIEF Event brief ¶2 [block 298c39a7-ff6a-49a9-a259-bfbc100124b1] (retrieved 2026-10-07T21:20:22.451Z) |
| `N-CAL-CAL-006` | Claim (calendar-constraint, supported): SRC-CALENDAR 'Calendar Constraints'!A7:H7 (retrieved 2026-10-07T21:20:22.884Z) |
| `N-CAL-CAL-007` | Claim (calendar-constraint, supported): SRC-CALENDAR 'Calendar Constraints'!A8:H8 (retrieved 2026-10-07T21:20:22.884Z) |
| `N-FP-FP-accessible-elevator-ev13` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.35–0.38, y 0.32–0.36 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-accessible-elevator-ev9` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.79–0.83, y 0.59–0.66 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-accessible-elevators-south` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.58–0.71, y 0.69–0.74 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-accessible-restroom-south` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.48–0.52, y 0.74–0.80 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-emergency-exits` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.40–0.88, y 0.08–0.80 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-hall-wheelchair-areas` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.70–0.79, y 0.29–0.59 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-legend` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.06–0.20, y 0.12–0.71 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-plenary-hall` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.58–0.88, y 0.23–0.64 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-room-401` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.44–0.53, y 0.32–0.54 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-title-block` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.92–0.99, y 0.55–0.99 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-FP-FP-vip-room` | Claim (floor-plan-observation, supported): SRC-TICC-4F page 1, x 0.29–0.42, y 0.40–0.68 (fractions of page from top-left) (retrieved 2026-10-07T21:20:30.017Z) |
| `N-QUOTE-Q-001` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A2:J2 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-QUOTE-Q-003` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A4:J4 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-QUOTE-Q-004` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A5:J5 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-QUOTE-Q-005` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A6:J6 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-QUOTE-Q-006` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A7:J7 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-QUOTE-Q-009` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A10:J10 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-QUOTE-Q-010` | Claim (vendor-quote, supported): SRC-VENDOR 'Vendor Quotes'!A11:J11 (retrieved 2026-10-07T21:20:24.281Z) |
| `N-VENUE-official_rule_livestream_contract_vendors_only` | Claim (venue-rule, supported): SRC-TICC-HALL 注意事項 (notes) › item 9 (retrieved 2026-10-07T21:20:25.437Z) |
| `N-VENUE-official_rule_technical_and_safety_briefing` | Claim (venue-rule, supported): SRC-TICC-HALL 注意事項 (notes) › item 10 (retrieved 2026-10-07T21:20:25.437Z) |
| `NOTE-vendor-experience` | Phase 3 note: Vendor experience / familiar-supplier status is not evidenced by any disclosed source; it is noted qualitatively and not scored. |
| `NOTE-venue-tariff` | Phase 3 note: Planning uses the negotiated case amount TWD 155000 (Q-001, full-day package). The official published weekend rate is TWD 170000 per time slot. The amounts are  |
| `OPT-2026-10-17-Q-003` | Phase 3 option: 2026-10-17 base bundle with catering Q-003: conditional |
| `OPT-2026-10-17-Q-003-add-Q-008` | Phase 3 option: 2026-10-17 base bundle with catering Q-003 plus add-on Q-008: infeasible |
| `OPT-2026-10-17-Q-003-sub-Q-007` | Phase 3 option: 2026-10-17 base bundle with catering Q-003, Q-007 instead of Q-006: infeasible |
| `OPT-2026-10-17-Q-004` | Phase 3 option: 2026-10-17 base bundle with catering Q-004: conditional |
| `OPT-2026-10-17-Q-004-add-Q-008` | Phase 3 option: 2026-10-17 base bundle with catering Q-004 plus add-on Q-008: infeasible |
| `OPT-2026-10-17-Q-004-sub-Q-007` | Phase 3 option: 2026-10-17 base bundle with catering Q-004, Q-007 instead of Q-006: infeasible |
| `OPT-2026-10-24-fallback` | Phase 3 option: 2026-10-24 fallback date: infeasible |
| `PD-break-count` | Programme planner decision (pending Programme review): Two breaks, matching the quoted catering package (lunch and two breaks). |
| `PD-break-minutes` | Programme planner decision (pending Programme review): Each of the two breaks lasts 15 minutes. |
| `PD-closing-minutes` | Programme planner decision (pending Programme review): Closing lasts 15 minutes and ends at the event window close. |
| `PD-demo-grouping` | Programme planner decision (pending Programme review): Demos are split into two groups around lunch; the first group takes the larger half when the count is odd, and roster order is kept. |
| `PD-lunch-minutes` | Programme planner decision (pending Programme review): Lunch lasts 60 minutes. |
| `PD-opening-minutes` | Programme planner decision (pending Programme review): Opening/welcome lasts 15 minutes, starting at the event window opening. |
| `PD-order` | Programme planner decision (pending Programme review): Order: opening; keynote at its fixed time; break 1; first half of the demos (roster order); lunch; second half of the demos (roster order); break 2; closing at  |
| `PRG-01-setup` | Programme block: Setup and pre-opening readiness checks 07:30–09:30 |
| `PRG-02-opening` | Programme block: Opening and welcome 09:30–09:45 |
| `PRG-03-buffer` | Programme block: Unallocated Programme buffer 09:45–10:00 |
| `PRG-04-keynote` | Programme block: Keynote 10:00–11:00 |
| `PRG-05-break` | Programme block: Break 1 11:00–11:15 |
| `PRG-06-demo` | Programme block: DEMO-01 presentation 11:15–11:25 |
| `PRG-07-changeover` | Programme block: DEMO-01 changeover 11:25–11:28 |
| `PRG-08-demo` | Programme block: DEMO-02 presentation 11:28–11:38 |
| `PRG-09-changeover` | Programme block: DEMO-02 changeover 11:38–11:41 |
| `PRG-10-demo` | Programme block: DEMO-03 presentation 11:41–11:51 |
| `PRG-11-changeover` | Programme block: DEMO-03 changeover 11:51–11:54 |
| `PRG-12-demo` | Programme block: DEMO-04 presentation 11:54–12:04 |
| `PRG-13-changeover` | Programme block: DEMO-04 changeover 12:04–12:07 |
| `PRG-14-demo` | Programme block: DEMO-05 presentation 12:07–12:17 |
| `PRG-15-changeover` | Programme block: DEMO-05 changeover 12:17–12:20 |
| `PRG-16-demo` | Programme block: DEMO-06 presentation 12:20–12:30 |
| `PRG-17-changeover` | Programme block: DEMO-06 changeover 12:30–12:33 |
| `PRG-18-lunch` | Programme block: Lunch 12:33–13:33 |
| `PRG-19-demo` | Programme block: DEMO-07 presentation 13:33–13:43 |
| `PRG-20-changeover` | Programme block: DEMO-07 changeover 13:43–13:46 |
| `PRG-21-demo` | Programme block: DEMO-08 presentation 13:46–13:56 |
| `PRG-22-changeover` | Programme block: DEMO-08 changeover 13:56–13:59 |
| `PRG-23-demo` | Programme block: DEMO-09 presentation 13:59–14:09 |
| `PRG-24-changeover` | Programme block: DEMO-09 changeover 14:09–14:12 |
| `PRG-25-demo` | Programme block: DEMO-10 presentation 14:12–14:22 |
| `PRG-26-changeover` | Programme block: DEMO-10 changeover 14:22–14:25 |
| `PRG-27-demo` | Programme block: DEMO-11 presentation 14:25–14:35 |
| `PRG-28-changeover` | Programme block: DEMO-11 changeover 14:35–14:38 |
| `PRG-29-demo` | Programme block: DEMO-12 presentation 14:38–14:48 |
| `PRG-30-changeover` | Programme block: DEMO-12 changeover 14:48–14:51 |
| `PRG-31-break` | Programme block: Break 2 14:51–15:06 |
| `PRG-32-buffer` | Programme block: Unallocated Programme buffer 15:06–16:45 |
| `PRG-33-closing` | Programme block: Closing 16:45–17:00 |
| `PRG-34-teardown` | Programme block: Teardown; all vendors clear 17:00–18:30 |
| `SRC-ATTENDEE` | Captured source: Project C — Attendee Signals (Google Sheet) (retrieved) |
| `SRC-BRIEF` | Captured source: Project C event brief (Notion page) (retrieved) |
| `SRC-BUDGET` | Captured source: Project C — Budget (Google Sheet) (retrieved) |
| `SRC-CALENDAR` | Captured source: Project C — Calendar Constraints (Google Sheet) (retrieved) |
| `SRC-TICC-4F` | Captured source: TICC official 4F accessible facilities floor plan (PDF) (retrieved) |
| `SRC-TICC-ACCESS` | Captured source: TICC official accessibility index (accessible facilities floor plans) (retrieved) |
| `SRC-TICC-HALL` | Captured source: TICC official Plenary Hall venue page (retrieved) |
| `SRC-VENDOR` | Captured source: Project C — Vendor Quotes (Google Sheet) (retrieved) |
| `STK-I1-L41` | Stakeholder interview interviews/project-c-event-coordination-20261007-1818.md line 41: "fellows, partners, staff, speakers, and forecast walk-ins are separate groups, and accessibility requests are overlapping needs, not additio" |
| `STK-I1-L87` | Stakeholder interview interviews/project-c-event-coordination-20261007-1818.md line 87: "It does not include accessibility needs as additional people, as those are overlapping needs." |
| `STK-I2-L53` | Stakeholder interview interviews/project-c-event-coordination-20261007-1855.md line 53: "Communications and contingency amounts are definitely part of the overall five hundred twenty thousand TWD planning ceiling." |
| `STK-I2-L65` | Stakeholder interview interviews/project-c-event-coordination-20261007-1855.md line 65: "Whether fifteen extra spots are sufficient as a buffer is a planning decision rather than a hard rule." |
| `STK-I2-L77` | Stakeholder interview interviews/project-c-event-coordination-20261007-1855.md line 77: "A hearing loop is part of our hard accessibility requirements." |
| `STK-I3-L181` | Stakeholder interview interviews/project-c-event-coordination-20261007-1931.md line 181: "Using the exact retrieval date and timestamp is the correct way to identify those sources, rather than using a content hash." |
| `STK-I3-L193` | Stakeholder interview interviews/project-c-event-coordination-20261007-1931.md line 193: "You should treat the floor plan solely as spatial evidence and rely on the separate coordination records for specific details like the numbe" |
| `STK-I3-L205` | Stakeholder interview interviews/project-c-event-coordination-20261007-1931.md line 205: "You should continue using the budgeted figure for planning and note the difference for documentation." |
| `STK-I3-L25` | Stakeholder interview interviews/project-c-event-coordination-20261007-1931.md line 25: "Therefore, an option relying on a "held" status cannot be called feasible until it is explicitly confirmed." |
| `STK-I3-L49` | Stakeholder interview interviews/project-c-event-coordination-20261007-1931.md line 49: "Without evidence of completion or confirmation, those dependencies—like the accessibility walkthrough or network test—mean the option remain" |
| `TO-catering_buffer` | Phase 4 factor comparison: the larger catering capacity buffer: OPT-2026-10-17-Q-003 = 15, OPT-2026-10-17-Q-004 = 55 |
| `TO-cost` | Phase 4 factor comparison: lower cost and greater budget headroom: OPT-2026-10-17-Q-003 = 494000, OPT-2026-10-17-Q-004 = 512000 |
| `TO-open_conditions` | Phase 4 factor comparison: fewer open condition types: OPT-2026-10-17-Q-003 = 8, OPT-2026-10-17-Q-004 = 8 |
| `TO-quote_validity` | Phase 4 factor comparison: all quotes valid through the decision deadline: OPT-2026-10-17-Q-003 = True, OPT-2026-10-17-Q-004 = True |
| `TO-unverified_checks` | Phase 4 factor comparison: fewer unverified checks: OPT-2026-10-17-Q-003 = 0, OPT-2026-10-17-Q-004 = 0 |
| `UNR-feasible-option-shortfall` | Phase 3 unresolved item: The brief asks for 2 feasible options; 0 are feasible on current evidence. No option is upgraded and none is fabricated. |
| `X-hold-vs-deadline` | Claim (cross-check, supported): SRC-CALENDAR 'Calendar Constraints'!A4:H4 (retrieved 2026-10-07T21:20:22.884Z); SRC-CALENDAR 'Calendar Constraints'!A6:H6 (retrieved 2026-10-07T21:20:22.884Z) |
