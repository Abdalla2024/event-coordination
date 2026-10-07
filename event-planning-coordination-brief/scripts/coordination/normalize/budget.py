"""Budget categories -> one claim per category. No spending room is derived here (STK-I1-L213 names
the inputs, not the formula)."""

from __future__ import annotations

from .base import Claim, held_claims, table_usable, unavailable_claim

SID = "SRC-BUDGET"


def normalize(captured) -> list[Claim]:
    ok, status = table_usable(captured, SID)
    if not ok:
        return [unavailable_claim("N-BUD-source", "budget-category", "Budget categories", SID, status)]
    parsed = captured[SID].parsed
    obs = {o["record_key"]: o["id"] for o in parsed.observations}
    claims = []
    for cat, row in parsed.records.items():
        value = {"category": cat, "planned_amount_twd": row["planned_amount_twd"],
                 "approval_limit_twd": row["approval_limit_twd"],
                 "committed_amount_twd": row["committed_amount_twd"], "owner": row["owner"]}
        claims.append(Claim(
            f"N-BUD-{cat}", "budget-category",
            f"{cat}: planned {row['planned_amount_twd']}, approval limit {row['approval_limit_twd']}, "
            f"committed {row['committed_amount_twd']} TWD; owner {row['owner']}",
            value, "supported", "retrieved", [obs[cat], "STK-I1-L213"], [SID], owner=row["owner"],
            fields={"currency": "TWD", "currency_basis": "column names end in _twd",
                    "record_version": row["record_version"],
                    "approval_limit_below_planned": row["approval_limit_twd"] < row["planned_amount_twd"]}))
    claims += held_claims(captured, SID, "N-BUD", "budget-category")
    return claims
