"""Capture every disclosed source and parse what was retrieved into observations.

Produces the schema `sourceRecord`s that snapshot 02 will carry. A source that fails retrieval or
parsing is still reported, with its attempts and issues; nothing is substituted for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import brief, sheets, ticc
from .capture import SourceCapture, capture_source, source_record
from .transport import Transport


@dataclass
class CapturedSource:
    capture: SourceCapture
    record: dict                 # schema sourceRecord
    parsed: object | None        # TableParse | BriefParse | dict | None
    issues: list[dict]


def _floor_plan_url(sources: list[dict]) -> str | None:
    return next((s["disclosed_url"] for s in sources if s["source_role"] == "floor-plan-or-image"), None)


def capture_all(sources: list[dict], profiles: dict, transport: Transport,
                deliverables_root: Path) -> dict[str, CapturedSource]:
    out: dict[str, CapturedSource] = {}
    for src in sources:
        cap = capture_source(src, profiles, transport, deliverables_root)
        body = cap.body(deliverables_root)
        observations, issues, native, parsed = [], [], None, None
        if body is not None:
            try:
                kind = src["retrieval"]["kind"]
                if "table" in src:
                    parsed = sheets.parse_table(src["id"], body, src["table"])
                    observations = parsed.observations
                    issues = [i.as_record(src["id"]) for i in parsed.issues]
                    if parsed.native_versions:
                        native = {"record_version": parsed.native_versions}
                elif kind == "notion-page-chunk":
                    parsed = brief.parse_brief(body, src["retrieval"]["notion_page_id"])
                    observations, issues, native = parsed.observations, parsed.issues, parsed.native_version
                elif src["id"] == "SRC-TICC-HALL":
                    observations, issues = ticc.parse_hall(body)
                elif src["id"] == "SRC-TICC-ACCESS":
                    observations, issues = ticc.parse_access_index(
                        body, src["retrieval"]["request_url"], _floor_plan_url(sources))
                elif src["retrieval"]["content_kind"] == "pdf":
                    native = ticc.pdf_metadata(body)
                    observations = [{
                        "id": f"OBS-{src['id']}-document",
                        "summary": "Official floor-plan PDF retained as evidence bytes; spatial observations "
                                   "are recorded separately against this file's hash.",
                        "locator": {"kind": "page-region", "value": "page 1, whole page"},
                    }]
            except Exception as exc:  # a parse failure is recorded, never hidden
                issues = [{"id": f"ISS-{src['id']}-parse", "kind": "table-parse-failure",
                           "summary": f"Retrieved content could not be parsed: {type(exc).__name__}: {exc}",
                           "evidence_ids": [src["id"]], "locator": "document"}]
                observations, parsed = [], None
        rec = source_record(cap, observations, native, issues)
        if any(i["kind"] == "table-parse-failure" for i in issues):
            rec["retrieval_status"] = "invalid"  # bytes arrived but cannot be interpreted
        out[src["id"]] = CapturedSource(cap, rec, parsed, issues)
    return out
