# Decision and feasibility model

`scripts/coordination/decide/` turns normalized claims into a planning baseline, candidate options,
per-option checks and a feasibility classification. It reads claims only, never raw sources. It is
deterministic, and it classifies and compares without ranking or recommending: the recommendation is a
separate layer, `recommend.py` (`recommendation-policy.md`) [S STK-I3-L85, STK-I3-L97]. Classification follows `decision-policy.md`.

Labels: **[S]** stakeholder · **[SRC]** source claim · **[A]** assignment · **[INT]** interpretation.

## Baseline (`B-*`)

Each element names the claims it rests on. If any of them is not `supported`, the element is
`unresolved`, carries no value, and lists `blocked_by`. Checks that use it become `unverified`.

| Element | Built from |
|---|---|
| `B-headcount` | Sum of the five attendee groups; needs are not added [S STK-I1-L41, STK-I1-L87] |
| `B-need-*` | Overlapping needs: wheelchair, companions, captions, hearing loop, quiet room, dietary, severe allergy |
| `B-event-window`, `B-fallback-window`, `B-keynote`, `B-venue-hold`, `B-teardown`, `B-decision-deadline` | Calendar rows, found through their role claims |
| `B-venue-coverage`, `B-readiness`, `B-time-requirements`, `B-programme` | Brief case records |
| `B-ceiling`, `B-budget-*`, `B-allowances` | Brief ceiling; budget rows; allowance categories at their planned amounts [S STK-I2-L53] |
| `B-accessibility-requirements` | Hearing loop, step-free access, wheelchair seating, live captions, staffed quiet room [S STK-I2-L77] |

## Candidate options

Each step of generation is traceable to claims:

1. **Base:** the venue quote for the readiness date, plus each catering alternative, plus the common services named in the readiness confirmation [SRC].
2. **Substitute:** another quote in the same category as a common service, on the same date, that is not an add-on (Q-007 for Q-006).
3. **Add-on:** a quote whose package says "add-on" (Q-008), added to each base. Treating the package wording as the add-on marker is [INT]; the readiness record calls the livestream optional [SRC].
4. **Fallback date:** the venue quote for the fallback window plus any services quoted for that date. Categories with no quote become `service_gaps`; nothing is filled in.

## Checks per option

Each check records the decision, outcome, evidence (claim and baseline ids), owner, and a reason
whenever it does not pass.

| Check | pass | otherwise |
|---|---|---|
| `date` | Option date is a calendar event window | `fail` if not a window |
| `keynote` | The hard keynote row is on the option date | `fail` on another date; cites CAL-004 and quote facts |
| `venue-window` | Venue hold (or the case coverage record) covers the date and 07:30–18:30 | `unverified` |
| `readiness` | The readiness record confirms exactly this bundle on this date | `open` for a quote the record names as unresolved (Q-008); `unverified` otherwise (Q-007: no vendor durations exist to derive it) |
| `service-*` | — | `unverified` for each category with no quote on the date |
| `<Q>-date` | — | `fail` if a quote is for another date |
| `<Q>-validity` | Valid at the business clock | `unverified` if expired; a quote expiring before the decision deadline is noted |
| `<Q>-terms` | — | `unverified` if the quote conflicts with another quote or with its own notes |
| `<Q>-confirmation` | Confirmation evidence recorded | `open` for held or available [S STK-I3-L25]. Venue quotes use `P-venue-confirmation` instead |
| `capacity-*` | Supply ≥ demand (venue places, catering vs all 245 [S STK-I3-L133], quiet room, wheelchair spaces, captions, hearing loop, security) | `fail` on a shortage; `unverified` if an input is not supported |
| `access-*` | Each hard provision evidenced | `fail` if missing or explicitly excluded (Q-007 hearing loop); `unverified` if spatial evidence is withheld or the date has no services |
| `dietary` | Case record covers documented dietary needs and the counts agree | `unverified` |
| `P-*` | Completion evidence recorded | `open` [S STK-I3-L49, STK-I3-L61] |
| `budget-<category>` | Amount ≤ approval limit; the variance from planned is noted [S STK-I2-L41] | `open` above the limit [S STK-I3-L73] |
| `budget-ceiling` | Quotes + allowances ≤ ceiling | `fail` above the ceiling; `unverified` if the total cannot be stated |
| `budget-commitments` | — | `unverified` if any committed amount is non-zero: no source defines how commitments combine with quotes, so no formula is invented |

## Costs

All amounts are integer TWD, computed per category from the option's quotes. Allowances are added at
their planned amounts. When an option has service gaps, `vendor_total_twd` and
`total_with_allowances_twd` are `null` with an `incomplete_reason`; a partial sum is never shown as a
total. The venue cost is the negotiated case amount; the official tariff is a note
(`NOTE-venue-tariff`) and never replaces it [S STK-I3-L205].

## Outputs

- **options** (schema `optionRecord`): feasibility, quotes, costs, blocking reasons by outcome, approval ids.
- **checks**: every check, with `option_id`.
- **approvals** (schema `approvalRecord`): Operations plan/date/venue, plus one per spending category including the allowances. All `pending`; `explicit_required` when a category exceeds its limit.
- **dependencies**: each open or unverified check across options, with owner, affected options and `deadline: null`.
- **unresolved**: blocked baseline elements, generation issues, and `UNR-feasible-option-shortfall` when fewer options are feasible than the brief requested. The shortfall is never covered by upgrading or inventing an option [A ASG-NO-INVENT].
- **comparison**: deterministic facts for every non-infeasible option (total, remaining ceiling, catering buffer, variances, open conditions). No weights and no ranking. Vendor experience is "not evidenced; not scored" [S STK-I3-L121].
- **recommendation**: `null` here. The recommendation layer (`recommendation-policy.md`) reads these results without changing them.
