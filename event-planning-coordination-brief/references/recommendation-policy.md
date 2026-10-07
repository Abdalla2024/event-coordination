# Recommendation policy

`scripts/coordination/recommend.py` compares the options that the decision layer
(`decision-model.md`) left `conditional` or `feasible`. It reads the decision model and never changes
option statuses, costs, checks or approvals. It is deterministic.

## No weights

The stakeholder gave no fixed ordering of cost, capacity buffer and vendor experience, and weighs them
against the current risks [S STK-I3-L85, STK-I3-L97]. The skill therefore uses **no weights, scores,
rankings or formula**. A preference is stated only by **dominance**; otherwise the choice goes to Operations.

## Candidates

- Eligible: options with status `conditional` or `feasible`.
- Excluded: `infeasible` and `unverified` options, each kept with its reason (the decision layer's rationale). A cheaper excluded option never becomes a candidate.

## Factors

Each factor records the values, the direction, the evidence, and a pairwise result for every pair of
candidates: `better`, `worse`, `tie` or `not-comparable`.

| Factor | Direction | Value |
|---|---|---|
| `cost` | lower total is better | Total including allowances; remaining room under the ceiling shown beside it |
| `catering_buffer` | larger is better | Catering capacity minus headcount. Limitation: the source does not define who the quoted capacity covers [S STK-I3-L133] |
| `open_conditions` | fewer is better | Count of normalized condition types (below) |
| `unverified_checks` | fewer is better | Count of the option's unverified checks |
| `quote_validity` | all valid is better than not all | Whether every quote in the option is valid through the decision deadline |

A missing or unsupported value makes the pair `not-comparable`.

**Not factors:** category variances are reported facts, not preferences. Vendor experience is not
evidenced and never scored [S STK-I3-L121].

## Normalized condition types

Open checks are compared by type, not by check id or prose, so the same underlying condition is counted once:

- Named prerequisites keep their id (`P-venue-confirmation`, `P-ticc-technical-safety-briefing`, …).
- A held or available quote's confirmation is typed by service category (`confirmation:catering`), so Q-003 and Q-004 confirmations are the same type.
- A quote's own outstanding condition (status `conditional`, or readiness left open because of that quote) is folded into the named prerequisites for the same quote, e.g. Q-008's network test.
- A category above its approval limit is `explicit-approval:<category>`.

## Outcome

| Outcome | When | Recommendation |
|---|---|---|
| `recommended` | One candidate dominates and it is `feasible` | that option |
| `recommended-conditional` | One candidate dominates and it is `conditional`; or it is the only eligible candidate | that option, labelled conditional, with every open condition type and its owners. A sole candidate is stated to be "the only recommendable option" |
| `deferred-to-operations` | No candidate dominates (factors favour different candidates, or a factor is not comparable) | `null`. Operations judgment is required; the tradeoff and question are stated |
| `no-viable-option` | No eligible candidate | `null`. The excluded options, shortfall and unresolved items are carried forward |

**Dominance:** a candidate is at least as good as every other candidate on every factor and strictly
better on at least one. Any `not-comparable` result rules dominance out.

The decision record (`DEC-recommendation`) is owned by Operations and keeps `approval_status: pending`.
Approvals are never granted here.

## Stakeholder context (informs statements, never weights)

- STK-I2-L65: a smaller buffer may require earlier refreshing if registrations increase. The walk-in forecast and its confidence are attached as factual context.
- STK-I1-L111: balance shortages against budget waste.
- STK-I3-L85, STK-I3-L97: no rigid order; weigh the current risks.
- STK-I3-L121: vendor experience is not scored without records.

## Run status

Execution status is kept separate from the business decision:

| Run status | Meaning |
|---|---|
| `complete` | Analysis done and a justified recommendation produced (`recommended` or `recommended-conditional`); approvals may remain pending |
| `partial` | Analysis done, but the outcome is `deferred-to-operations` or `no-viable-option`, or a source was not retrieved |
| `blocked` | A required prerequisite stopped the analysis (no options could be generated) |
| `failed` | The workflow itself failed. Reserved for execution errors; a deferral is never a failure |
