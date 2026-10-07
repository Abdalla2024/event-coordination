"""Change impact derived from the existing evidence links (no separate dependency model).

For each captured source, follow evidence references forward (source -> claims -> baseline -> checks
-> options -> recommendation, approvals, programme) and report what would need reconsidering.
"""

from __future__ import annotations

from collections import defaultdict

SECTION_RULES = (  # (id prefix or marker, sections)
    (("B-headcount", "B-need-"), ("event-plan §3 headcount",)),
    (("B-event-window", "B-fallback-window", "B-keynote", "B-venue-hold", "B-teardown", "B-decision-deadline",
      "B-readiness", "B-programme", "B-time-requirements", "PRG-"), ("event-plan §4 timing and run of show",
                                                                       "event-calendar.ics")),
    (("B-budget-", "B-ceiling", "B-allowances"), ("event-plan §5 budget",)),
    (("B-accessibility", "N-FP-"), ("event-plan §7 accessibility",)),
    (("OPT-",), ("vendor-comparison.csv", "event-plan §6 options", "draft-communications.md")),
    (("TO-", "DEC-"), ("event-plan §8 recommendation",)),
    (("APR-",), ("event-plan §13 approvals", "draft-communications.md")),
)


def _nodes(ri) -> dict[str, list[str]]:
    d, rec, prog = ri.decision, ri.recommendation, ri.programme
    nodes: dict[str, list[str]] = {}
    for c in ri.claims:
        nodes[c["id"]] = list(c["evidence_ids"]) + list(c.get("source_ids", []))
    for group in ("baseline", "checks", "options", "approvals", "dependencies", "unresolved", "comparison", "notes"):
        for r in d[group]:
            nodes[r["id"]] = list(r["evidence_ids"])
    for f in rec["factors"]:
        nodes[f["id"]] = list(f["evidence_ids"])
    nodes[rec["decision"]["id"]] = list(rec["decision"]["evidence_ids"])
    for b in prog["blocks"]:
        nodes[b["id"]] = b["evidence_ids"] + b["decision_ids"]
    return nodes


def build(ri) -> dict:
    nodes = _nodes(ri)
    dependents = defaultdict(set)
    for n, evidence in nodes.items():
        for e in evidence:
            dependents[e].add(n)
    # observations belong to their source
    for s in ri.sources:
        for o in s.get("observations", []):
            dependents[s["id"]] |= dependents.get(o["id"], set())
    out = {}
    for s in ri.sources:
        seen, stack = set(), [s["id"]]
        while stack:
            for nxt in dependents.get(stack.pop(), ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        sections = []
        for prefixes, secs in SECTION_RULES:
            if any(i.startswith(prefixes) for i in seen):
                sections += [x for x in secs if x not in sections]
        if any(i.startswith("CHK-") and "-budget-" in i for i in seen) and "event-plan §5 budget" not in sections:
            sections.append("event-plan §5 budget")
        if any(i.startswith("CHK-") and "-access-" in i for i in seen) and "event-plan §7 accessibility" not in sections:
            sections.append("event-plan §7 accessibility")
        out[s["id"]] = {"claims": sum(1 for i in seen if i.startswith(("N-", "X-", "P-"))),
                        "options": sorted(i for i in seen if i.startswith("OPT-")),
                        "sections": sections}
    return out
