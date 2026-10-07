# Decision policy

The rules the skill applies, each traced to its basis. IDs in brackets resolve in
`requirements-evidence.json` (STK-*, ASG-*) or name the planning source that supplies the value at run time (SRC-*).

Labels: **[S]** stakeholder interview · **[A]** assignment · **[SRC]** source content read at run time · **[INT]** implementation interpretation · **[UNK]** unresolved.

## Values are read, never hard-coded

Amounts, dates, capacities, the ceiling, the roster and calendar windows come from the sources captured
in the current run. This file states how to *interpret* them. If a required value is missing,
duplicated or invalid, its record is held and anything that depends on it is reported as unverified [A ASG-CHANGED-INPUTS].

## Option feasibility

Each option is evaluated against a list of checks. Every check ends in one of four outcomes:
`pass`, `fail`, `open` (a required condition is not yet evidenced) or `unverified` (evidence missing or invalid).

| Option status | Condition | Basis |
|---|---|---|
| `infeasible` | Any check `fail`: a hard constraint is broken and cannot be cleared | [S STK-I1-L103] |
| `unverified` | No `fail`, but a check is `unverified`: evidence is missing, unavailable, invalid, stale or conflicting | [S STK-I1-L127], [A ASG-TRACE] |
| `conditional` | No `fail` or `unverified`, but at least one check is `open` | [S STK-I3-L25, STK-I3-L49, STK-I3-L61, STK-I3-L73] |
| `feasible` | Every check `pass`, **including every confirmation and prerequisite check** | [S STK-I3-L25, STK-I3-L49] |

Precedence when several apply: infeasible > unverified > conditional > feasible [INT]. All failing,
unverified and open checks are reported, not only the one that decides the status.

An option with no checks is `unverified`, never `feasible` [INT].

### Checks that are `open` until evidence exists

- **Vendor or venue status `held` or `available`.** These are planning states, not bookings, so the check stays `open` until explicit confirmation evidence is recorded [S STK-I2-L113, STK-I3-L25]. The plan must name each such hold [S STK-I3-L37].
- **Vendor status `conditional`.** An outstanding required condition [S STK-I2-L101].
- **Venue confirmation** [S STK-I3-L61].
- **Accessibility walkthrough, TICC technical coordination meeting and safety evacuation briefing, severe-allergy contact coordination, livestream network test** [S STK-I3-L49, STK-I3-L61].
- **Category amount above its approval limit while the total is within the ceiling.** Needs explicit owner approval [S STK-I3-L73, STK-I1-L221].

A label or number never counts as confirmation [A ASG-NO-INFER]. Completion is shown only by a
recorded evidence item or an actual human response, recorded with actor, subject, plan revision, timestamp, outcome and reasons [SRC SRC-BRIEF venue coordination record].

### Checks that `fail`

- Outside the hard date, event, keynote, venue or teardown windows [SRC SRC-CALENDAR], [S STK-I1-L249].
- Missing a hard accessibility service: hearing loop, step-free access, wheelchair seating, live captions, staffed quiet room [S STK-I2-L77].
- Total including the communications and contingency allowances above the planning ceiling [S STK-I2-L53], [SRC SRC-BRIEF].
- Required capacity is below the population it must serve, with no alternative inside the option [S STK-I1-L103, STK-I3-L133].

### Budget checks

- Category amount at or below the approval limit: `pass`, with the variance from the planned amount recorded. Ordinary approval from the budget owner is still `pending` [S STK-I2-L41].
- Above the approval limit, total within the ceiling: `open` [S STK-I3-L73].
- Total above the ceiling: `fail` [S STK-I2-L53].

### Quote validity

Validity is judged at the business clock (`references/run-config.json`), not the retrieval date [A ASG-CLOCK]. A `valid_until` date with no time is treated as valid through the end of that day, Asia/Taipei [INT]. An expired quote is not assumed: the dependent check is `unverified` until a refreshed quote is captured [SRC SRC-BRIEF], [INT].

## Headcount

- The groups (fellows, partners, staff, speakers, forecast walk-ins) are kept separate and summed. Accessibility and dietary requests overlap these groups and are never added [S STK-I1-L41, STK-I1-L87].
- Catering capacity is compared with the full headcount, staff and speakers included. Who each quote's capacity covers is checked against that package's details. Where the package details do not say, the limitation is recorded [S STK-I3-L133].
- Any headcount change re-runs every capacity comparison [S STK-I3-L145].

## Option comparison and recommendation

1. Hard constraints come first [S STK-I2-L89].
2. Among non-infeasible options, weigh cost, capacity buffer and vendor experience. There are **no numerical weights and no fixed order** [S STK-I3-L85]. The recommendation is a reasoned judgment of the most critical current risks [S STK-I3-L97], recorded as a decision record with rationale and tradeoffs.
3. Vendor experience comes from past run-of-show records, which no disclosed source provides [S STK-I3-L109]. It is mentioned as unevidenced and **never scored** [S STK-I3-L121].
4. A recommendation may name a `conditional` option only if it is labelled conditional and lists its open checks. Otherwise the recommendation is deferred [INT].
5. A second feasible option is never fabricated. If fewer feasible options exist than the brief asks for, that shortfall is an unresolved item owned by Operations [SRC SRC-BRIEF], [A ASG-NO-INVENT].

## Venue evidence

- The official 4F floor plan is **spatial evidence only**. Wheelchair-space counts and hearing-loop availability come from the coordination record in the brief [S STK-I3-L193].
- The negotiated case venue amount from the vendor register is the planning value. The official published TICC tariff is recorded beside it as a documented difference and never replaces it [S STK-I3-L205].
- Official venue rules that create prerequisites, such as the Plenary Hall technical coordination meeting and safety evacuation briefing, become `open` prerequisite checks owned by Operations, **with no invented deadline** [S STK-I3-L157, STK-I3-L169].

## Source identity and versions

- Sources with no native version are identified by their exact retrieval timestamp [S STK-I3-L181]. Any native version is recorded beside it: the brief's version line and record IDs, or the sheets' `record_version`.
- A sha256 content hash is still recorded for every captured byte stream, as an integrity check required by the assignment and schema, not as the version identifier [A ASG-EXTRACTS], [INT].

## Retrieval

- Every attempt is recorded, including rejected and failed ones, with request URL, profile, time, HTTP result, outcome, reason, hash and the stored response bytes [A ASG-CAPTURE].
- For the TICC pages a plain request is tried first. If the site rejects it, one browser-like retry is made and recorded as a separate attempt. The rejected attempt is kept [INT, decided by the learner after the requirements review].
- A source that cannot be retrieved is `unavailable` or `invalid`. Its dependent claims are withheld or marked unverified, and independent work continues [A ASG-TRACE].

## Approvals and actions

Every approval is `pending` unless an actual human response is recorded. The skill never books, pays,
invites, commits to vendors, writes to production calendars, changes approvals, or publishes private
contact or medical details [S STK-I1-L151], [A ASG-DRAFT-ONLY, ASG-PRIVACY].
