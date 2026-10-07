"""Candidate options derived from the evidence, and their deterministic cost arithmetic.

Generation rule (each step traceable to claims):
- Base bundles for the readiness date: the venue quote for that date + each catering alternative + the
  common services named by the readiness confirmation (N-BRIEF-readiness_base_bundles).
- Substitutes: another supported quote in the same category as a common service, on the same date,
  that is not an add-on (e.g. Q-007 for Q-006).
- Add-ons: a supported quote whose package says "add-on" (e.g. Q-008), added to each base bundle.
- Fallback date: the venue quote for the fallback window plus whatever services are quoted for that
  date; services with no quote on that date are listed as gaps, never filled in.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Option:
    id: str
    label: str
    variant: str                      # base | substitute | add-on | fallback-date
    date: str
    quote_ids: list[str]
    service_gaps: list[str] = field(default_factory=list)   # categories with no quote on the date
    derived_from: list[str] = field(default_factory=list)   # claim/baseline ids behind the composition


def _is_addon(q) -> bool:
    return "add-on" in q.value["package"].lower()


def generate(baseline) -> tuple[list[Option], list[dict]]:
    """Return (options, generation_issues). Issues are records explaining options that could not be built."""
    quotes, issues, options = baseline.quotes, [], []
    ready = baseline.get("B-readiness")
    win, fall = baseline.get("B-event-window"), baseline.get("B-fallback-window")
    if ready is None or win is None:
        issues.append({"id": "GEN-base", "summary": "Base bundles cannot be generated: readiness confirmation or "
                       "preferred window is not supported.", "evidence_ids": ["B-readiness", "B-event-window"],
                       "owner": "Operations", "rationale": None})
        return options, issues
    date = win["date"]

    def venue_on(day):
        v = [q for q in quotes.values() if q.value["category"] == "venue" and q.value["available_date"] == day]
        return v

    venues = venue_on(date)
    if len(venues) != 1:
        issues.append({"id": f"GEN-venue-{date}", "summary": f"{len(venues)} supported venue quotes for {date}; "
                       "a single venue quote is required to build options and none is chosen.",
                       "evidence_ids": [q.id for q in venues] or ["B-event-window"], "owner": "Operations",
                       "rationale": None})
        return options, issues
    venue = venues[0].value["quote_id"]
    common = list(ready["common"])
    derived = ["B-readiness", "B-event-window", venues[0].id]
    bases = []
    for cat_q in ready["catering_alternatives"]:
        oid = f"OPT-{date}-{cat_q}"
        o = Option(oid, f"{date} base bundle with catering {cat_q}", "base", date, [venue, cat_q, *common],
                   derived_from=derived)
        options.append(o)
        bases.append(o)
    for base in bases:
        for member in common:
            m = quotes.get(member)
            if m is None:
                continue
            for q in sorted(quotes):
                c = quotes[q]
                if (q not in base.quote_ids and c.value["category"] == m.value["category"]
                        and c.value["available_date"] == date and not _is_addon(c)):
                    options.append(Option(f"{base.id}-sub-{q}", f"{base.label}, {q} instead of {member}",
                                          "substitute", date, [x if x != member else q for x in base.quote_ids],
                                          derived_from=derived + [c.id]))
        for q in sorted(quotes):
            c = quotes[q]
            if _is_addon(c) and c.value["available_date"] == date:
                options.append(Option(f"{base.id}-add-{q}", f"{base.label} plus add-on {q}", "add-on", date,
                                      base.quote_ids + [q], derived_from=derived + [c.id]))
    if fall is not None:
        fdate = fall["date"]
        fv = venue_on(fdate)
        needed = {quotes[q].value["category"] for q in [*ready["catering_alternatives"], *common] if q in quotes}
        on_day = [q for q, c in sorted(quotes.items()) if c.value["available_date"] == fdate and not _is_addon(c)
                  and c.value["category"] != "venue"]
        gaps = sorted(needed - {quotes[q].value["category"] for q in on_day})
        options.append(Option(f"OPT-{fdate}-fallback", f"{fdate} fallback date", "fallback-date", fdate,
                              [q.value["quote_id"] for q in fv] + on_day, service_gaps=gaps,
                              derived_from=["B-fallback-window"] + [q.id for q in fv]))
    return options, issues


def costs(option: Option, baseline) -> dict:
    """Integer TWD arithmetic: quote amounts by category, plus allowances, against the ceiling.

    No spending-room formula is applied; committed amounts are reported, not combined.
    """
    by_cat: dict[str, dict] = {}
    for q in option.quote_ids:
        v = baseline.quotes[q].value
        entry = by_cat.setdefault(v["category"], {"quote_ids": [], "amount_twd": 0})
        entry["quote_ids"].append(q)
        entry["amount_twd"] += int(v["amount_twd"])
    allowances = baseline.get("B-allowances")
    quoted = sum(e["amount_twd"] for e in by_cat.values())
    ceiling = baseline.get("B-ceiling")
    reasons = []
    if option.service_gaps:
        reasons.append(f"no quotes for {option.service_gaps} on {option.date}")
    if allowances is None:
        reasons.append("budget allowances not supported")
    complete = not reasons
    vendor_total = quoted if not option.service_gaps else None
    total = vendor_total + sum(allowances.values()) if complete else None
    return {
        "currency": "TWD",
        "categories": by_cat,
        "quoted_amount_twd": quoted,
        "vendor_total_twd": vendor_total,
        "allowances_twd": allowances,
        "total_with_allowances_twd": total,
        "ceiling_twd": ceiling,
        "remaining_under_ceiling_twd": ceiling - total if (ceiling is not None and total is not None) else None,
        "committed_amounts_twd": baseline.commitments,
        "complete": complete,
        "incomplete_reason": "; ".join(reasons) or None,
    }
