"""Evidence citation helper shared by the Markdown renderers.

Renderers cite existing ids only. The appendix resolves each cited id to the record it names:
a claim's source, locator and retrieval time; a model record; a stakeholder line; a planner decision.
"""

from __future__ import annotations

from ..config import load_requirements_evidence


class Citations:
    def __init__(self, ri):
        self.ri = ri
        self.cited: list[str] = []
        self.claims = {c["id"]: c for c in ri.claims}
        self.records = {}
        d = ri.decision
        for group, label in (("baseline", "Phase 3 baseline"), ("checks", "Phase 3 check"),
                             ("options", "Phase 3 option"), ("approvals", "Phase 3 approval (pending)"),
                             ("dependencies", "Phase 3 dependency"), ("unresolved", "Phase 3 unresolved item"),
                             ("comparison", "Phase 3 comparison facts"), ("notes", "Phase 3 note")):
            for r in d[group]:
                self.records[r["id"]] = (label, r["summary"])
        rec = ri.recommendation
        for f in rec["factors"]:
            self.records[f["id"]] = ("Phase 4 factor comparison", f["summary"])
        self.records[rec["decision"]["id"]] = ("Phase 4 decision record", rec["decision"]["summary"])
        for c in rec["stakeholder_context"]:
            self.records[c["id"]] = ("Phase 4 stakeholder context", c["summary"])
        for d_ in ri.programme["decisions"]:
            self.records[d_["id"]] = ("Programme planner decision (pending Programme review)", d_["summary"])
        for b in ri.programme["blocks"]:
            self.records[b["id"]] = ("Programme block", f"{b['label']} {b['start'][11:16]}–{b['end'][11:16]}")
        for s in ri.sources:
            self.records[s["id"]] = ("Captured source", f"{s['summary']} ({s['retrieval_status']})")
        self.requirements = load_requirements_evidence()

    def __call__(self, *ids) -> str:
        ids = [i for i in dict.fromkeys(ids) if i]
        for i in ids:
            if i not in self.cited:
                self.cited.append(i)
        return f"_Evidence: {', '.join(ids)}_" if ids else ""

    def known(self, i: str) -> bool:
        return i in self.claims or i in self.records or i in self.requirements

    def describe(self, i: str) -> str:
        if i in self.claims:
            c = self.claims[i]
            prov = c.get("provenance") or []
            where = "; ".join(f"{p['source_id']} {p['locator']['value']} (retrieved {p['retrieved_at']})"
                              for p in prov[:2]) or "derived from other claims"
            return f"Claim ({c['kind']}, {c['support']}): {where}"
        if i in self.records:
            label, summary = self.records[i]
            return f"{label}: {summary[:160]}"
        if i in self.requirements:
            r = self.requirements[i]
            if r["group"] == "stakeholder":
                return f"Stakeholder interview {r['interview']} line {r['line']}: \"{r['quote'][:140]}\""
            return f"Assignment ({r['section']}): \"{r['quote'][:140]}\""
        return "UNRESOLVED REFERENCE"

    def appendix(self) -> str:
        rows = ["| ID | Resolves to |", "|---|---|"]
        rows += [f"| `{i}` | {self.describe(i).replace('|', '/')} |" for i in sorted(self.cited)]
        return "\n".join(rows)
