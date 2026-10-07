"""Official TICC sources: venue page, accessibility index, 4F floor-plan PDF.

Only facts printed on the pages are extracted, each with a section locator. The floor plan's spatial
observations need visual reading and are supplied separately (reasoning step), bound to the PDF hash.
"""

from __future__ import annotations

import html as htmlmod
import re
from urllib.parse import urljoin

_TAGS = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)


def page_text(raw: bytes) -> list[str]:
    """Visible text lines of an HTML page, in document order."""
    text = _DROP.sub(" ", raw.decode("utf-8", errors="replace"))
    text = htmlmod.unescape(_TAGS.sub("\n", text))
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def page_title(raw: bytes) -> str | None:
    m = re.search(rb"<title>(.*?)</title>", raw, re.S | re.I)
    return htmlmod.unescape(m.group(1).decode("utf-8", "replace")).strip() if m else None


def _after(lines: list[str], label: str) -> str | None:
    for i, ln in enumerate(lines):
        if ln == label and i + 1 < len(lines):
            return lines[i + 1]
    return None


def _amount(text: str | None) -> int | None:
    m = re.fullmatch(r"([\d,]+)\s*元", text or "")
    return int(m.group(1).replace(",", "")) if m else None


def parse_hall(raw: bytes) -> tuple[list[dict], list[dict]]:
    """Return (observations, issues) for the Plenary Hall page."""
    lines, obs, issues = page_text(raw), [], []

    def add(oid, summary, locator, **extra):
        obs.append({"id": f"OBS-SRC-TICC-HALL-{oid}", "summary": summary,
                    "locator": {"kind": "section", "value": locator}, **extra})

    title = page_title(raw)
    if title:
        add("title", f"Page title: {title}", "<title>")
    seats = next((m for ln in lines if (m := re.search(r"固定座位共([\d,]+)席", ln))), None)
    if seats:
        add("fixed-seats", f"Plenary Hall has {seats.group(1)} fixed seats (official page).",
            "空間簡介 (venue introduction)", value=int(seats.group(1).replace(",", "")))
    slots = _after(lines, "每時段租金")
    weekday = _amount(_after(lines, "週一～週五"))
    weekend = _amount(_after(lines, "週六～週日"))
    if slots:
        add("rate-slots", f"Published rental is per time slot: {slots}.", "每時段租金 (rental per time slot)",
            value=slots)
    for oid, label, amount, day in (("rate-weekday", "週一～週五", weekday, "Monday–Friday"),
                                    ("rate-weekend", "週六～週日", weekend, "Saturday–Sunday")):
        if amount is None:
            issues.append({"id": f"ISS-SRC-TICC-HALL-{oid}", "kind": "fact-not-found",
                           "summary": f"Published {day} rate not found on the page.",
                           "evidence_ids": ["SRC-TICC-HALL"], "locator": label})
        else:
            add(oid, f"Official published {day} rate: TWD {amount} per time slot.",
                f"每時段租金 › {label}", value=amount, currency="TWD", unit="per time slot")
    for num, oid, topic in (("9", "rule-livestream", "livestream"),
                            ("10", "rule-briefing", "technical coordination and safety briefing")):
        rule = next((ln for ln in lines if re.match(rf"^{num}\.\s*\S", ln)), None)
        if rule:
            add(oid, f"Venue rule {num} ({topic}): {rule}", f"注意事項 (notes) › item {num}", text=rule)
        else:
            issues.append({"id": f"ISS-SRC-TICC-HALL-{oid}", "kind": "fact-not-found",
                           "summary": f"Venue rule {num} ({topic}) not found on the page.",
                           "evidence_ids": ["SRC-TICC-HALL"], "locator": "注意事項"})
    return obs, issues


def parse_access_index(raw: bytes, base_url: str, floor_plan_url: str) -> tuple[list[dict], list[dict]]:
    """List the accessible-facilities plans and confirm the disclosed 4F PDF is among them."""
    html = raw.decode("utf-8", errors="replace")
    entries = []
    for href, label in re.findall(r'<a [^>]*href="([^"]+\.pdf)"[^>]*>(.*?)</a>', html, re.S | re.I):
        text = " ".join(htmlmod.unescape(_TAGS.sub(" ", label)).split())
        if "Accessible Facilities Floor Plan" in text:
            entries.append({"label": text, "url": urljoin(base_url, htmlmod.unescape(href))})
    obs = [{"id": "OBS-SRC-TICC-ACCESS-plans",
            "summary": f"Official index lists {len(entries)} accessible-facilities floor plans.",
            "locator": {"kind": "section", "value": "Accessible Facilities Floor Plan list"},
            "entries": entries}]
    issues = []
    match = [e for e in entries if e["url"] == floor_plan_url]
    if match:
        obs.append({"id": "OBS-SRC-TICC-ACCESS-4f",
                    "summary": f"The disclosed 4F PDF is listed as '{match[0]['label']}'.",
                    "locator": {"kind": "section", "value": f"Accessible Facilities Floor Plan list › {match[0]['label']}"},
                    "url": floor_plan_url})
    else:
        issues.append({"id": "ISS-SRC-TICC-ACCESS-4f", "kind": "fact-not-found",
                       "summary": "The disclosed 4F floor-plan PDF is not listed on the official index.",
                       "evidence_ids": ["SRC-TICC-ACCESS"], "locator": "Accessible Facilities Floor Plan list"})
    return obs, issues


def pdf_metadata(raw: bytes) -> dict:
    """Version facts readable without rendering: modification date and page count."""
    mod = re.search(rb"/ModDate\s*\(D:(\d{14})", raw)
    pages = len(re.findall(rb"/Type\s*/Page(?!s)", raw))
    out = {"page_count": pages or None}
    if mod:
        s = mod.group(1).decode()
        out["pdf_mod_date"] = f"{s[0:4]}-{s[4:6]}-{s[6:8]}T{s[8:10]}:{s[10:12]}:{s[12:14]}Z"
    return out
