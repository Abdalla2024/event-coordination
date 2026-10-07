from datetime import datetime

from conftest import xlsx_bytes
from coordination.sheets import parse_table

HEADER = ["quote_id", "vendor", "category", "option", "quote_amount_twd", "capacity",
          "available_date", "valid_until", "status", "notes"]
ROW1 = ["Q-1", "V", "venue", "pkg", 1000, 50, 46312, 46270, "held", ""]
ROW2 = ["Q-2", "W", "catering", "lunch", 2000.0, 60, "2026-10-17", "2026-09-07", "available", "n"]


def vendor_table(sources):
    return sources["SRC-VENDOR"]["table"]


def kinds(p):
    return sorted(i.kind for i in p.issues)


def test_reads_by_header_with_serial_and_iso_dates(sources):
    p = parse_table("S", xlsx_bytes([HEADER, ROW1, ROW2], "Vendor Quotes"), vendor_table(sources))
    assert p.issues == []
    assert p.records["Q-1"]["available_date"] == "2026-10-17"
    assert p.records["Q-1"]["valid_until"] == "2026-09-05"
    assert p.records["Q-2"]["quote_amount_twd"] == 2000
    assert p.observations[0]["locator"] == {"kind": "cell-range", "value": "'Vendor Quotes'!A2:J2"}


def test_reordered_headers_rows_and_extra_columns(sources):
    order = list(reversed(range(len(HEADER))))
    hdr = [HEADER[i] for i in order] + ["unrelated_extra"]
    rows = [[r[i] for i in order] + ["x"] for r in (ROW2, ROW1)]
    p = parse_table("S", xlsx_bytes([hdr] + rows, "Vendor Quotes"), vendor_table(sources))
    base = parse_table("S", xlsx_bytes([HEADER, ROW1, ROW2], "Vendor Quotes"), vendor_table(sources))
    assert p.issues == []
    assert p.records == base.records
    assert any(h["text"] == "unrelated_extra" for h in p.headers)  # captured representation kept


def test_header_case_and_spacing_tolerated_but_renames_are_not_guessed(sources):
    hdr = [" Quote_ID "] + HEADER[1:]
    assert parse_table("S", xlsx_bytes([hdr, ROW1], "Vendor Quotes"), vendor_table(sources)).issues == []
    renamed = ["quote_id", "vendor", "category", "option", "amount_twd"] + HEADER[5:]
    p = parse_table("S", xlsx_bytes([renamed, ROW1], "Vendor Quotes"), vendor_table(sources))
    assert p.held and p.records == {} and kinds(p) == ["table-missing-header"]


def test_duplicate_ids_are_held_not_chosen(sources):
    dup = list(ROW2)
    dup[0] = "Q-1"
    p = parse_table("S", xlsx_bytes([HEADER, ROW1, dup], "Vendor Quotes"), vendor_table(sources))
    assert "Q-1" not in p.records and kinds(p) == ["duplicate-id"]


def test_invalid_row_with_same_id_makes_identity_ambiguous(sources):
    bad = list(ROW1)
    bad[4] = "lots"
    p = parse_table("S", xlsx_bytes([HEADER, ROW1, bad], "Vendor Quotes"), vendor_table(sources))
    assert "Q-1" not in p.records
    assert kinds(p) == ["duplicate-id", "invalid-row"]


def test_invalid_values_hold_the_row(sources):
    bad_amount = list(ROW2); bad_amount[4] = 12.5
    bad_status = list(ROW2); bad_status[0] = "Q-3"; bad_status[8] = "booked"
    blank_req = list(ROW2); blank_req[0] = "Q-4"; blank_req[5] = None
    negative = list(ROW2); negative[0] = "Q-5"; negative[4] = -1
    p = parse_table("S", xlsx_bytes([HEADER, ROW1, bad_amount, bad_status, blank_req, negative],
                                    "Vendor Quotes"), vendor_table(sources))
    assert set(p.records) == {"Q-1"}
    assert kinds(p) == ["invalid-row"] * 4


def test_duplicate_header_holds_table(sources):
    p = parse_table("S", xlsx_bytes([HEADER + ["status"], ROW1 + ["held"]], "Vendor Quotes"),
                    vendor_table(sources))
    assert p.held and p.records == {}


def test_hidden_rows_and_columns(sources):
    p = parse_table("S", xlsx_bytes([HEADER, ROW1, ROW2], "Vendor Quotes", hidden_rows=[3]),
                    vendor_table(sources))
    assert set(p.records) == {"Q-1"} and kinds(p) == ["hidden-row"]
    p = parse_table("S", xlsx_bytes([HEADER, ROW1], "Vendor Quotes", hidden_cols=["E"]),
                    vendor_table(sources))
    assert p.held and kinds(p) == ["table-hidden-column"]


def test_sheet_selection(sources):
    t = vendor_table(sources)
    p = parse_table("S", xlsx_bytes([HEADER, ROW1], "Renamed"), t)
    assert set(p.records) == {"Q-1"} and kinds(p) == ["sheet-renamed"]
    p = parse_table("S", xlsx_bytes([HEADER, ROW1], "Other", extra_sheets=[("Another", "visible")]), t)
    assert p.held and kinds(p) == ["table-missing-sheet"]


def test_calendar_requires_offsets_and_ordering(sources):
    t = sources["SRC-CALENDAR"]["table"]
    hdr = ["constraint_id", "owner", "constraint_type", "start_at", "end_at", "priority", "notes", "record_version"]
    good = ["C-1", "Ops", "window", "2026-10-17T09:30:00+08:00", "2026-10-17T17:00:00+08:00", "hard", "", "v1"]
    naive = ["C-2", "Ops", "window", "2026-10-17T09:30:00", "2026-10-17T17:00:00+08:00", "hard", "", "v1"]
    backwards = ["C-3", "Ops", "window", "2026-10-17T17:00:00+08:00", "2026-10-17T09:30:00+08:00", "soft", "", "v1"]
    naive_dt = ["C-4", "Ops", "window", datetime(2026, 10, 17, 9, 30), "2026-10-17T17:00:00+08:00", "hard", "", "v1"]
    p = parse_table("S", xlsx_bytes([hdr, good, naive, backwards, naive_dt], "Calendar Constraints"), t)
    assert set(p.records) == {"C-1"} and kinds(p) == ["invalid-row"] * 3
    assert p.native_versions == ["v1"]


def test_mixed_record_versions_flagged(sources):
    t = sources["SRC-BUDGET"]["table"]
    hdr = ["category", "planned_amount_twd", "approval_limit_twd", "committed_amount_twd", "owner", "record_version"]
    p = parse_table("S", xlsx_bytes([hdr, ["venue", 1, 2, 0, "Ops", "b-1"], ["catering", 1, 2, 0, "Ops", "b-2"]],
                                    "Budget"), t)
    assert len(p.records) == 2 and kinds(p) == ["mixed-record-versions"]
