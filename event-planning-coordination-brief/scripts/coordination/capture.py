"""Source retrieval with every attempt recorded.

Each disclosed source is requested through its registered route. Every attempt, including rejected
and failed ones, keeps its request, timing, HTTP result, outcome, reason and response bytes. Only a
plain request is tried first; a browser-like retry happens only for sources that list it and only
after the site rejected the plain request.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .transport import HttpRequest, HttpResponse, Transport
from .util import atomic_write, sha256_bytes, utc_now

EXTENSIONS = {"xlsx": "xlsx", "notion-json": "json", "html": "html", "pdf": "pdf"}
CONTENT_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "notion-json": "application/json",
    "html": "text/html",
    "pdf": "application/pdf",
}
REJECTION_TITLE = re.compile(rb"<title>\s*Request Rejected\s*</title>", re.I)

# Attempt outcomes and the schema retrieval_status each one leads to.
OUTCOME_TO_STATUS = {
    "retrieved": "retrieved",
    "rejected": "unavailable",
    "http-error": "unavailable",
    "network-error": "unavailable",
    "invalid-content": "invalid",
}


@dataclass
class Attempt:
    attempt_id: str
    source_id: str
    sequence: int
    profile: str
    method: str
    request_url: str
    request_headers: dict
    started_at: str
    completed_at: str
    http_status: int | None
    response_content_type: str | None
    final_url: str | None
    byte_length: int
    sha256: str | None
    local_reference: str | None
    outcome: str
    reason: str
    response_headers: dict = field(default_factory=dict)

    def as_record(self) -> dict:
        return {
            "id": self.attempt_id,
            "summary": f"{self.profile} {self.method} attempt {self.sequence}: {self.outcome} ({self.reason})",
            "evidence_ids": [],
            "source_id": self.source_id,
            "sequence": self.sequence,
            "profile": self.profile,
            "method": self.method,
            "request_url": self.request_url,
            "request_headers": self.request_headers,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "http_status": self.http_status,
            "response_content_type": self.response_content_type,
            "response_last_modified": self.response_headers.get("last-modified"),
            "response_etag": self.response_headers.get("etag"),
            "final_url": self.final_url,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "local_reference": self.local_reference,
            "outcome": self.outcome,
            "reason": self.reason,
        }


@dataclass
class SourceCapture:
    source: dict
    attempts: list[Attempt]

    @property
    def accepted(self) -> Attempt | None:
        for a in self.attempts:
            if a.outcome == "retrieved":
                return a
        return None

    @property
    def final(self) -> Attempt:
        return self.accepted or self.attempts[-1]

    @property
    def retrieval_status(self) -> str:
        return OUTCOME_TO_STATUS[self.final.outcome]

    def body(self, deliverables_root: Path) -> bytes | None:
        a = self.accepted
        return (Path(deliverables_root) / a.local_reference).read_bytes() if a else None


def build_request(source: dict, profile_headers: dict) -> HttpRequest:
    r = source["retrieval"]
    if r["kind"] == "notion-page-chunk":
        payload = {"pageId": r["notion_page_id"], "limit": 500, "cursor": {"stack": []},
                   "chunkNumber": 0, "verticalColumns": False}
        headers = {**profile_headers, "Content-Type": "application/json"}
        return HttpRequest("POST", r["request_url"], headers, json.dumps(payload).encode())
    return HttpRequest("GET", r["request_url"], dict(profile_headers))


def assess(source: dict, resp: HttpResponse) -> tuple[str, str]:
    """Classify one response as (outcome, reason). Pure function of the response."""
    kind = source["retrieval"]["content_kind"]
    if resp.status is None:
        return "network-error", resp.error or "no response"
    if REJECTION_TITLE.search(resp.body[:2000]):
        return "rejected", f"HTTP {resp.status} with a site 'Request Rejected' page"
    if resp.status in (401, 403, 429):
        return "rejected", f"HTTP {resp.status}"
    if resp.status != 200:
        return "http-error", f"HTTP {resp.status}"
    if not resp.body:
        return "invalid-content", "empty body"
    if kind == "xlsx":
        try:
            with zipfile.ZipFile(io.BytesIO(resp.body)) as z:
                if "xl/workbook.xml" not in z.namelist():
                    return "invalid-content", "zip without xl/workbook.xml"
        except zipfile.BadZipFile:
            return "invalid-content", "not an xlsx workbook (possibly a sign-in page)"
        return "retrieved", "xlsx workbook"
    if kind == "pdf":
        if not resp.body.startswith(b"%PDF-"):
            return "invalid-content", "body is not a PDF"
        return "retrieved", "PDF document"
    if kind == "notion-json":
        try:
            data = json.loads(resp.body)
        except ValueError:
            return "invalid-content", "body is not JSON"
        blocks = (data.get("recordMap") or {}).get("block") or {}
        if source["retrieval"]["notion_page_id"] not in blocks:
            return "invalid-content", "page block missing from response"
        if (data.get("cursor") or {}).get("stack"):
            return "invalid-content", "response truncated: further chunks required"
        return "retrieved", f"Notion page data with {len(blocks)} blocks"
    if kind == "html":
        text = resp.body.decode("utf-8", errors="replace")
        missing = [m for m in source["retrieval"].get("expected_markers", []) if m not in text]
        if missing:
            return "invalid-content", f"expected content not found: {missing}"
        return "retrieved", "HTML page with expected content"
    raise ValueError(f"unknown content kind {kind}")


def capture_source(source: dict, profiles: dict, transport: Transport, deliverables_root: Path,
                   evidence_rel: str = "snapshots/evidence",
                   clock: Callable[[], str] = utc_now) -> SourceCapture:
    sid = source["id"]
    kind = source["retrieval"]["content_kind"]
    attempts: list[Attempt] = []
    for seq, profile in enumerate(source["retrieval"]["profiles"], start=1):
        if attempts and attempts[-1].outcome != "rejected":
            break  # fall back only when the site rejected the previous request
        req = build_request(source, profiles[profile]["headers"])
        started = clock()
        resp = transport(req)
        completed = clock()
        outcome, reason = assess(source, resp)
        attempt_id = f"ATT-{sid}-{seq}"
        local_ref = digest = None
        if resp.body:
            ext = EXTENSIONS[kind] if outcome == "retrieved" else _ext_for(resp)
            local_ref = f"{evidence_rel}/{sid}/{attempt_id}.{ext}"
            digest = sha256_bytes(resp.body)
            atomic_write(Path(deliverables_root) / local_ref, resp.body)
        attempts.append(Attempt(
            attempt_id=attempt_id, source_id=sid, sequence=seq, profile=profile, method=req.method,
            request_url=req.url, request_headers=dict(req.headers), started_at=started,
            completed_at=completed, http_status=resp.status,
            response_content_type=resp.headers.get("content-type"), final_url=resp.final_url,
            byte_length=len(resp.body), sha256=digest, local_reference=local_ref,
            outcome=outcome, reason=reason, response_headers=resp.headers))
    return SourceCapture(source, attempts)


def _ext_for(resp: HttpResponse) -> str:
    ctype = (resp.headers.get("content-type") or "").lower()
    if "html" in ctype:
        return "html"
    if "json" in ctype:
        return "json"
    if "pdf" in ctype:
        return "pdf"
    return "bin"


def source_record(cap: SourceCapture, observations: list[dict], native_version: dict | None,
                  issues: list[dict] | None = None) -> dict:
    """Schema `sourceRecord` for snapshot 02.

    Version identity follows the stakeholder rule (STK-I3-L181): the exact retrieval timestamp.
    The content hash is kept as an integrity check.
    """
    src, final, ok = cap.source, cap.final, cap.accepted
    return {
        "id": src["id"],
        "summary": src["title"],
        "evidence_ids": [a.attempt_id for a in cap.attempts] + list(src.get("meaning_evidence", [])),
        "owner": None,
        "rationale": src["stakeholder_meaning"],
        "source_role": src["source_role"],
        "locator": src["disclosed_url"],
        "retrieved_at": final.completed_at,
        "retrieval_status": cap.retrieval_status,
        "content_type": CONTENT_TYPES[src["retrieval"]["content_kind"]] if ok else (final.response_content_type or "none"),
        "version_metadata": {
            "version_basis": "retrieval_timestamp",
            "version_basis_evidence": "STK-I3-L181",
            "retrieved_at": final.completed_at,
            "native_version": native_version or None,
            "http_last_modified": final.response_headers.get("last-modified"),
        },
        "content_hash": ok.sha256 if ok else None,
        "local_reference": ok.local_reference if ok else None,
        "observations": observations,
        "disclosed_in": src["disclosed_in"],
        "retrieval_route": src["retrieval"]["kind"],
        "attempts": [a.as_record() for a in cap.attempts],
        "parse_issues": issues or [],
    }
