"""Event brief (Notion page data) -> ordered, section-located text blocks.

Phase 1 extracts the brief's structure, text and native version identifiers. Interpreting the prose
into constraints is done in later stages; every later claim cites a block observation from here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

HEADING_TYPES = {"header", "sub_header", "sub_sub_header"}
VERSION_PATTERNS = {
    "brief_version": r"Brief version:\s*([A-Z0-9][\w-]*)",
    "venue_record": r"Record:\s*(VEN-[\w-]+?)[;\s]",
    "venue_clarification": r"Coordination clarification:\s*(VEN-[\w-]+?)[;\s]",
    "programme_clarification": r"Programme clarification:\s*(PROG-[\w-]+?)[;\s]",
}


@dataclass
class BriefParse:
    page_id: str
    title: str
    blocks: list[dict]
    observations: list[dict]
    native_version: dict
    issues: list[dict] = field(default_factory=list)


def _value(entry: dict) -> dict:
    v = entry.get("value", {}) if isinstance(entry, dict) else {}
    return v.get("value", v) if isinstance(v, dict) and "type" not in v else v


def _text(rich) -> str:
    return "".join(seg[0] for seg in rich or [] if seg and isinstance(seg[0], str))


def parse_brief(body: bytes, page_id: str) -> BriefParse:
    data = json.loads(body)
    blocks = data["recordMap"]["block"]
    page = _value(blocks[page_id])
    if not isinstance(page, dict) or page.get("type") != "page" or not page.get("content"):
        raise ValueError(f"block {page_id} is not a page with content")
    title = _text(page.get("properties", {}).get("title"))
    out, observations, issues = [], [], []
    section, para = title, 0

    def walk(ids, depth=0):
        nonlocal section, para
        for bid in ids:
            if bid not in blocks:
                issues.append({"id": f"ISS-SRC-BRIEF-missing-{bid[:8]}", "kind": "missing-block",
                               "summary": f"Child block {bid} not present in page data.",
                               "evidence_ids": ["SRC-BRIEF"], "locator": bid})
                continue
            b = _value(blocks[bid])
            btype = b.get("type")
            text = _text(b.get("properties", {}).get("title"))
            if btype in HEADING_TYPES:
                section, para = text, 0
            elif text:
                para += 1
            n = len(out) + 1
            locator = f"{section} ¶{para}" if btype not in HEADING_TYPES else f"{section} (heading)"
            entry = {"index": n, "block_id": bid, "type": btype, "section": section,
                     "paragraph": para if btype not in HEADING_TYPES else None, "text": text}
            out.append(entry)
            if text:
                observations.append({
                    "id": f"OBS-SRC-BRIEF-B{n:02d}",
                    "summary": text if len(text) <= 240 else text[:237] + "...",
                    "locator": {"kind": "section", "value": f"{locator} [block {bid}]"},
                    "block_id": bid,
                    "text": text,
                })
            walk(b.get("content", []), depth + 1)

    walk(page.get("content", []))

    full = "\n".join(b["text"] for b in out)
    native = {}
    for key, pattern in VERSION_PATTERNS.items():
        found = sorted(set(re.findall(pattern, full + "\n")))
        if len(found) == 1:
            native[key] = found[0]
        elif len(found) > 1:
            native[key] = found
            issues.append({"id": f"ISS-SRC-BRIEF-multi-{key}", "kind": "ambiguous-version",
                           "summary": f"More than one {key} found: {found}.",
                           "evidence_ids": ["SRC-BRIEF"], "locator": "brief"})
    if page.get("last_edited_time"):
        native["notion_last_edited"] = datetime.fromtimestamp(
            page["last_edited_time"] / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    if page.get("version") is not None:
        native["notion_page_version"] = page["version"]
    return BriefParse(page_id, title, out, observations, native, issues)
