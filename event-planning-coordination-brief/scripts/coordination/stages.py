"""The nine stage snapshots, built from the outputs the earlier phases already produced.

No value is computed here: each snapshot packages existing records (source records, claims, baseline,
programme, options, checks, recommendation, render manifest) and declares what it consumed and
produced. `SnapshotChain.write` enforces the schema, ordering, predecessor hashes, id bookkeeping and
evidence resolution.
"""

from __future__ import annotations

from .snapshots import SnapshotChain

SCHEDULE = ("B-event-window", "B-fallback-window", "B-keynote", "B-venue-hold", "B-teardown", "B-decision-deadline",
            "B-venue-coverage", "B-readiness", "B-time-requirements", "B-programme")
HARD_BRIEF = ("N-BRIEF-hard_requirements", "N-BRIEF-planning_ceiling_twd",
              "N-BRIEF-no_expired_quote_or_unconfirmed_availability", "N-BRIEF-conditional_not_feasible_rule")


def _ids(records) -> list[str]:
    return [r["id"] for r in records]


def _fallback(consumed: list[str], previous: list[str]) -> list[str]:
    """A transition must consume at least one earlier record; use the previous stage's first output if needed."""
    return list(dict.fromkeys(consumed)) or previous[:1]


def build(chain: SnapshotChain, inp: dict) -> list[dict]:
    """inp: sources, claims, decision, recommendation, run_status, programme, render_manifest, supersede."""
    claims, d, rec, prog = inp["claims"], inp["decision"], inp["recommendation"], inp["programme"]
    by_claim = {c["id"]: c for c in claims}
    base = {b["id"]: b for b in d["baseline"]}

    def cval(cid):
        c = by_claim.get(cid)
        return c["value"] if c and c["support"] == "supported" else None

    # 01 scope and approval gates -------------------------------------------------------------------
    sup = inp["supersede"]
    event = cval("N-BRIEF-event_name") or "the event"
    deadline = base.get("B-decision-deadline", {})
    owners = sorted({a["owner"] for a in d["approvals"] if a.get("owner")}
                    | {b["value"]["owner"] for k, b in base.items() if k.startswith("B-budget-") and b["support"] == "supported"})
    plan_approver = cval("N-BRIEF-plan_approver")
    gates = ([f"{plan_approver}: plan, date and venue approval (pending)"] if plan_approver else []) + \
            [f"{b['value']['owner']}: {k.removeprefix('B-budget-')} spending approval (pending)"
             for k, b in sorted(base.items()) if k.startswith("B-budget-") and b["support"] == "supported"]
    s01_records = [
        {"id": "S01-objective", "summary": f"Review-ready, draft-only plan for {event}: compare supported options, "
                                          "keep unconfirmed items conditional, return approvals to their owners.",
         "evidence_ids": ["STK-I1-L13", "STK-I1-L159", "ASG-DRAFT-ONLY"]},
        {"id": "S01-gates", "summary": "; ".join(gates) or "no approval gates established",
         "evidence_ids": ["STK-I1-L73"]},
        {"id": "S01-supersede", "summary": sup["reason"], "evidence_ids": ["ASG-HISTORY"],
         "supersedes_run_id": sup["supersedes_run_id"], "changed_ids": sup["changed_ids"]},
    ]
    state01 = {"objective": s01_records[0]["summary"], "owners": owners, "approval_gates": gates,
               "records": s01_records, "supersedes_run_id": sup["supersedes_run_id"],
               "changed_ids": sup["changed_ids"], "supersede_reason": sup["reason"], "recovery": sup["recovery"],
               "decision_deadline_basis": "calendar decision_deadline row, captured in snapshot 02"}
    if deadline.get("support") == "supported":
        state01["decision_deadline"] = deadline["value"]
    out = [chain.write("scope-and-approval-gates", "complete", state01, [], _ids(s01_records))]

    # 02 source capture ----------------------------------------------------------------------------
    sources = inp["sources"]
    all_retrieved = all(s["retrieval_status"] == "retrieved" for s in sources)
    out.append(chain.write("source-capture", "complete" if all_retrieved else "partial", {"sources": sources},
                           ["S01-objective"], _ids(sources)))

    # 03 constraint model --------------------------------------------------------------------------
    hard = [c for c in claims if (c["kind"] == "calendar-constraint" and c["support"] == "supported"
                                  and c["value"]["priority"] == "hard") or c["id"] in HARD_BRIEF
            or c["kind"] == "prerequisite"]
    soft = [c for c in claims if c["kind"] == "calendar-constraint" and c["support"] == "supported"
            and c["value"]["priority"] == "soft"]
    unknowns = [c for c in claims if c["support"] in ("unsupported", "unresolved")]
    conflicts = [c for c in claims if c["support"] == "conflicting"]
    state03 = {"hard_constraints": hard, "preferences": soft, "assumptions": prog["decisions"],
               "unknowns": unknowns, "conflicts": conflicts, "claims": claims,
               "assumption_note": "Assumptions are Programme planner decisions, kept separate from source facts."}
    retrieved = [s["id"] for s in sources if s["retrieval_status"] == "retrieved"]
    out.append(chain.write("constraint-model", "complete" if not (unknowns or conflicts) else "partial", state03,
                           _fallback(retrieved, _ids(sources)), _ids(claims) + _ids(prog["decisions"])))

    # 04 planning baseline -------------------------------------------------------------------------
    blocks = [{**b, "summary": f"{b['label']} {b['start']} – {b['end']} ({b['basis']})"} for b in prog["blocks"]]
    state04 = {
        "headcount_basis": [b for k, b in base.items() if k == "B-headcount" or k.startswith("B-need-")],
        "schedule_dependencies": [base[k] for k in SCHEDULE if k in base] + blocks,
        "budget_baseline": [b for k, b in base.items() if k.startswith(("B-budget-", "B-ceiling", "B-allowances"))],
        "accessibility_baseline": [b for k, b in base.items() if k == "B-accessibility-requirements"],
        "programme": {k: prog[k] for k in ("status", "reason", "date", "unallocated_minutes", "demo_count")},
    }
    produced_claims = set(_ids(claims))
    used = [e for b in d["baseline"] for e in b["evidence_ids"] if e in produced_claims]
    complete04 = all(b["support"] == "supported" for b in d["baseline"]) and prog["status"] == "planned"
    out.append(chain.write("planning-baseline", "complete" if complete04 else "partial", state04,
                           _fallback(used, _ids(claims)), list(base) + _ids(blocks)))

    # 05 option generation -------------------------------------------------------------------------
    gen_issues = [u for u in d["unresolved"] if u["id"].startswith("GEN-")]
    options = [{"id": o["id"], "summary": o["label"], "variant": o["variant"], "date": o["date"],
                "quote_ids": o["quote_ids"], "service_gaps": o["service_gaps"], "costs": o["costs"],
                "evidence_ids": [e for e in o["evidence_ids"] if not e.startswith("CHK-")] or ["B-event-window"]}
               for o in d["options"]]
    used = [e for o in options for e in o["evidence_ids"] if e in base or e in produced_claims]
    out.append(chain.write("option-generation", "complete" if options else "blocked",
                           {"options": options, "rejected_early": []}, _fallback(used, list(base)),
                           _ids(options) + _ids(gen_issues), unresolved=gen_issues))

    # 06 feasibility testing -----------------------------------------------------------------------
    state06 = {"option_results": d["options"], "unresolved_conditions": d["dependencies"], "checks": d["checks"],
               "comparison": d["comparison"]}
    out.append(chain.write("feasibility-testing", "complete" if options else "blocked", state06,
                           _fallback(_ids(options), _ids(gen_issues) or list(base)),
                           _ids(d["checks"]) + _ids(d["dependencies"]) + _ids(d["comparison"])))

    # 07 decision and approval ---------------------------------------------------------------------
    excluded = [{"id": f"EXC-{e['option_id']}", "summary": f"Not recommendable ({e['feasibility']}): {e['reason']}",
                 "evidence_ids": e["evidence_ids"]} for e in rec["excluded"]]
    earlier = set(_ids(gen_issues))
    unresolved07 = [u for u in d["unresolved"] if u["id"] not in earlier]
    state07 = {"recommendation": rec["recommendation"], "tradeoffs": rec["factors"],
               "learner_decisions": [rec["decision"]], "approval_requirements": d["approvals"],
               "recommendation_status": rec["status"], "question_for_operations": rec["question_for_operations"],
               "operations_judgment_required": rec["operations_judgment_required"],
               "excluded": excluded, "stakeholder_context": rec["stakeholder_context"], "notes": d["notes"]}
    status07 = ("complete" if rec["status"] in ("recommended", "recommended-conditional")
                else "blocked" if not options else "partial")
    produced07 = (_ids(rec["factors"]) + [rec["decision"]["id"]] + _ids(d["approvals"]) + _ids(excluded)
                  + _ids(rec["stakeholder_context"]) + _ids(d["notes"]) + _ids(unresolved07))
    out.append(chain.write("decision-and-approval", status07, state07,
                           _fallback(_ids(d["comparison"]) + _ids(options), _ids(d["checks"]) or list(base)),
                           produced07, unresolved=unresolved07, decisions=[rec["decision"]]))

    # 08 draft propagation -------------------------------------------------------------------------
    rm = inp["render_manifest"]
    drafts = [{k: a[k] for k in ("id", "path", "sha256", "validation_status")} for a in rm["artifacts"]]
    impacts = [{"id": f"IMP-{sid}", "summary": f"A change to {sid} affects {len(i['options'])} option(s) and "
                f"{', '.join(i['sections']) or 'no deliverable section'}.", "evidence_ids": [sid], **i}
               for sid, i in rm["impact"].items()]
    unresolved08 = list(d["unresolved"])
    if prog["status"] != "planned":
        unresolved08.append({"id": "UNR-programme", "summary": f"Run of show not planned: {prog['reason']}",
                             "evidence_ids": [rec["decision"]["id"]], "owner": "Programme"})
    out.append(chain.write("draft-propagation",
                           "complete" if all(a["validation_status"] == "valid" for a in drafts) else "failed",
                           {"artifact_drafts": drafts, "affected_dependencies": impacts,
                            "unresolved_items": unresolved08, "programme_status": prog["status"]},
                           [rec["decision"]["id"]] + _ids(d["approvals"]),
                           _ids(drafts) + _ids(impacts) + (["UNR-programme"] if prog["status"] != "planned" else [])))

    # 09 publication validation --------------------------------------------------------------------
    run_state = inp["run_status"]["status"]
    pubs = [{"id": f"PUB-{a['path']}", "path": a["path"], "sha256": a["sha256"],
             "validation_status": a["validation_status"]} for a in rm["artifacts"]]
    chain_check = {"id": "V-snapshots-01-08", "summary": "Snapshots 01–08 were written with schema validation, "
                   "predecessor hashes, consumed/produced bookkeeping and evidence resolution enforced.",
                   "evidence_ids": [rec["decision"]["id"]], "outcome": "pass"}
    checks = [{k: c[k] for k in ("id", "summary", "evidence_ids", "outcome")} for c in rm["validation_checks"]]
    publication = ("failed" if not rm["all_valid"] else "blocked" if run_state == "blocked" else "validated")
    out.append(chain.write("publication-validation", run_state,
                           {"artifacts": pubs, "validation_checks": checks + [chain_check],
                            "publication_status": publication, "run_status": inp["run_status"],
                            "recommendation_status": rec["status"]},
                           _ids(drafts), _ids(pubs) + _ids(checks) + [chain_check["id"]]))
    return out
