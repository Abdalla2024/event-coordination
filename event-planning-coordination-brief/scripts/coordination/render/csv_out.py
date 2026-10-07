"""vendor-comparison.csv: one row per Phase 3 option, in model order (never sorted by cost).

List and object cells are JSON. `cost_twd` is Phase 3 `total_with_allowances_twd`, the amount checked
against the ceiling; it is blank when the model could not state it, with the reason in `unresolved`.
"""

from __future__ import annotations

import csv
import io
import json

REQUIRED = ["option_id", "quote_ids", "planning_people", "cost_twd", "currency", "feasibility",
            "availability_status", "evidence_ids", "tradeoffs", "unresolved", "approval_status"]
EXTRA = ["option_label", "feasibility_reason", "quote_details", "vendor_total_twd", "allowances_twd",
         "remaining_under_ceiling_twd", "recommendation_outcome"]
COLUMNS = REQUIRED + EXTRA


def _j(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _int_or_blank(value) -> str:
    return "" if value is None else str(int(value))


def render(view: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    people = view["headcount"]["total"] if view["headcount"] else None
    outcome = view["recommendation"]["status"]
    for o in view["options"]:
        c = o["costs"]
        w.writerow([
            o["id"], _j(o["quote_ids"]), _int_or_blank(people),
            _int_or_blank(c["total_with_allowances_twd"]), c["currency"], o["feasibility"],
            _j(o["availability"]), _j(o["evidence_ids"]), _j(o["tradeoffs"]), _j(o["unresolved"]),
            "|".join(o["approval_status"]),
            o["label"], o["feasibility_reason"], _j(o["quote_details"]),
            _int_or_blank(c["vendor_total_twd"]), _j(c["allowances_twd"]),
            _int_or_blank(c["remaining_under_ceiling_twd"]), outcome,
        ])
    return buf.getvalue()
