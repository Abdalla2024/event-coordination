"""Required conditions disclosed by the sources and the stakeholder, each with completion state `open`.

No disclosed source records completion of any prerequisite, so none is marked complete. Completion
can only be added from a recorded evidence item or an actual human response in a later run.
"""

from __future__ import annotations

from .base import Claim
from .crosscheck import Claims


def _prereq(pid, name, owner, applies_to, basis, cs: Claims, detail=None, extra=None) -> Claim:
    present = [b for b in basis if not b.startswith(("N-", "X-")) or cs.val(b) is not None]
    missing = [b for b in basis if b.startswith(("N-", "X-")) and cs.val(b) is None]
    stakeholder = [b for b in basis if b.startswith("STK-")]
    fields = {"completion_state": "open", "completion_evidence": [], "applies_to": applies_to,
              "deadline": None, "deadline_basis": "none stated in any source; none is invented",
              **(extra or {})}
    if missing and not stakeholder:
        return Claim(pid, "prerequisite", f"{name}: basis not supported ({missing}); held.", None, "unresolved",
                     "unverified", [b for b in basis if cs.get(b) or not b.startswith(("N-", "X-"))] or ["ASG-TRACE"],
                     [], owner=owner, fields={**fields, "missing_basis": missing})
    sources = sorted({s for b in present if cs.get(b) for s in cs.get(b).source_ids})
    return Claim(pid, "prerequisite", f"{name}: required condition, open (no evidence of completion)."
                 + (f" {detail}" if detail else ""),
                 {"name": name, "completion_state": "open"}, "supported", "retrieved", present, sources,
                 owner=owner, rationale="Required conditions keep an option conditional until evidenced (STK-I3-L49).",
                 fields={**fields, **({"missing_basis": missing} if missing else {})})


def run(cs: Claims) -> list[Claim]:
    out = []
    venue = [c for c in cs.of_kind("vendor-quote") if c.value["category"] == "venue"]
    out.append(_prereq(
        "P-venue-confirmation", "Venue confirmation", cs.val("N-BRIEF-plan_approver") or "Operations",
        [c.value["quote_id"] for c in venue],
        ["STK-I3-L61", "STK-I3-L25", "STK-I3-L37"] + [c.id for c in venue], cs,
        detail="Venue quotes are " + ", ".join(f"{c.value['quote_id']} '{c.value['status']}'" for c in venue)
        + "; held and available are planning states, not bookings."))

    walk = cs.calendar_row("accessibility_walkthrough")
    out.append(_prereq(
        "P-accessibility-walkthrough", "Accessibility walkthrough",
        walk.value["owner"] if walk else None, ["all options"],
        ["STK-I3-L49"] + ([walk.id] if walk else ["N-CAL-ROLE-accessibility_walkthrough"]), cs,
        detail=(f"Calendar window {walk.value['start_at']} – {walk.value['end_at']}"
                + ("; venue confirmation required first." if walk.fields["note_facts"].get("requires_venue_confirmation_first") else ".")) if walk else None,
        extra={"scheduled_window": [walk.value["start_at"], walk.value["end_at"]] if walk else None,
               "depends_on": ["P-venue-confirmation"] if walk and walk.fields["note_facts"].get("requires_venue_confirmation_first") else []}))

    out.append(_prereq(
        "P-ticc-technical-safety-briefing", "TICC technical coordination meeting and safety evacuation briefing",
        "Operations", ["all options using the Plenary Hall"],
        ["N-VENUE-official_rule_technical_and_safety_briefing", "STK-I3-L157", "STK-I3-L169"], cs,
        detail="Timing is to be coordinated by Operations with the venue."))

    catering = [c for c in cs.of_kind("vendor-quote") if c.value["category"] == "catering"]
    named = [c.value["quote_id"] for c in catering if "named_allergy_contacts" in c.fields["prerequisites"]]
    out.append(_prereq(
        "P-severe-allergy-contacts", "Severe-allergy contact coordination",
        cs.val("N-BRIEF-named_contacts_holder") or "Operations", [c.value["quote_id"] for c in catering],
        ["STK-I3-L49", "STK-I2-L65", "N-BRIEF-named_contacts_holder", "N-ATT-need-severe_allergy_follow_up"]
        + [f"N-QUOTE-{q}" for q in named], cs,
        detail=f"Quotes whose notes require named contacts: {named or 'none'}. Contacts stay with Operations "
               "and are never copied into outputs.",
        extra={"quote_specific_requirement": named,
               "applies_to_basis": "stakeholder named severe-allergy coordination as a required condition "
                                   "(STK-I3-L49); applied to every catering option [INT]"}))

    stream = [c for c in cs.of_kind("vendor-quote") if "livestream_network_test" in c.fields["prerequisites"]]
    for c in stream:
        q = c.value["quote_id"]
        out.append(_prereq(f"P-livestream-network-test-{q}", f"Livestream network test for {q}", "Operations", [q],
                           ["STK-I3-L61", "STK-I1-L167", c.id], cs))
        out.append(_prereq(f"P-livestream-venue-confirmation-{q}", f"Venue confirmation for livestream {q}",
                           "Operations", [q], ["STK-I3-L61", c.id, "N-BRIEF-livestream_conditions",
                                               "N-VENUE-official_rule_livestream_contract_vendors_only"], cs))
    return out
