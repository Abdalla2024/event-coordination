# Normalized source data

`scripts/coordination/normalize/` turns captured and parsed sources into **claims**: one normalized
business fact each, linked to the evidence that supports it. Later stages read claims, never raw rows or prose.

## Evidence bytes vs normalized records

- **Evidence bytes** are the captured files under `snapshots/evidence/<SOURCE-ID>/`. Each is referenced by its source record's `local_reference` and `content_hash`.
- **Observations** are located extracts inside one capture: a sheet row (`cell-range`), a brief paragraph (`section`), a page fact (`section`), or a floor-plan region (`page-region`).
- **Claims** cite observation ids, stakeholder or assignment evidence (`STK-*`, `ASG-*`), parse issues (`ISS-*`) or other claims. `provenance` resolves every claim down to the source, locator, retrieval timestamp and native version. Claims never embed evidence bytes.

## Two status fields

| Field | Values | Meaning |
|---|---|---|
| `support` | `supported` | Read directly from current evidence. Only supported claims carry a `value`. |
| | `unsupported` | Expected but not found, or its source was not retrieved. |
| | `conflicting` | Evidence items disagree. Candidates are kept in `fields`; no value is chosen. |
| | `unresolved` | Evidence exists but cannot be interpreted safely (invalid, ambiguous, unmapped). Nothing is guessed. |
| `evidence_status` | `retrieved` / `unavailable` / `invalid` / `unverified` / `stale` | The schema retrieval vocabulary applied to the claim's evidence. `stale` marks a quote or hold that expired before the business clock. |

## Versions

Each claim's provenance carries the source's **retrieval timestamp**, which is the version identity the stakeholder asked for (STK-I3-L181), plus any **native version**: the brief's version line and record IDs, or the sheets' `record_version`. These are separate fields; one is never substituted for the other.

## Claim kinds

| Kind | From | Notes |
|---|---|---|
| `calendar-constraint`, `calendar-role` | Calendar | One claim per row. One role claim per expected constraint type; several rows of one type are `conflicting`, none is `unsupported`. Note text becomes facts by explicit pattern; anything unmatched is kept as `note_unparsed`. |
| `budget-category` | Budget | Planned, approval limit, committed, owner. No spending-room formula is derived. |
| `attendee-group`, `attendee-need`, `attendee-signal` | Attendee signals | Groups are separate populations (STK-I1-L41). Needs overlap them and have `counts_as_people: false` (STK-I1-L87). Unknown signals are held, not counted. Only aggregate counts are read; extra columns, which could hold personal data, are never carried. |
| `vendor-quote`, `quote-conflict`, `quote-validity` | Vendor register (+ calendar) | Comparable fields (amount, capacity, date, validity, category). `booking_state` is always a planning state or an outstanding condition, `confirmed: false`. Features, prerequisites and facts come from explicit note and option patterns, each with its matched text. Unmatched note text and option/note disagreements are recorded. `capacity_population` stays null: the register does not say who a capacity covers (STK-I3-L133). |
| `brief-fact` | Event brief | Each fact comes from an explicit pattern with its matched text. Repeated equal mentions are `supported`; different values are `conflicting`; a vanished pattern is `unsupported`. `case_record: true` marks facts from the fictional venue, readiness or programme records. |
| `venue-fact`, `venue-rule` | TICC pages | Official real-venue facts. Rates have `replaces_case_amount: false`. |
| `floor-plan-observation` | 4F floor plan + `floorplan-observations.json` | Spatial only (STK-I3-L193). `supported` only when the captured PDF hash matches the hash the observations were read against. On a mismatch they are held as `unverified`; if the plan is unavailable they are withheld. Ambiguous readings are `unresolved`. Bound observations are added to the PDF's source record with page-region locators. |
| `cross-check` | Two or more sources | `supported` = consistent; `conflicting` = inconsistent, both sides kept, owner Operations; `unresolved` = an input is not supported. |
| `documented-difference` | Vendor + calendar + TICC page | The negotiated case venue amount next to the official tariff; the planning value is never replaced (STK-I3-L205). |
| `prerequisite` | Stakeholder + sources | Required conditions with `completion_state: open`, `completion_evidence: []` and `deadline: null`. They stay open until a recorded evidence item or actual human response closes them (STK-I3-L49, STK-I3-L61, STK-I3-L169). |

## Read-only

Normalization only reads captured records and reference files. It has no network, messaging,
booking, payment or calendar-write code; a test enforces this.
