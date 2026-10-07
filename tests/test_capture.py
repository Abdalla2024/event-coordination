import json

from conftest import FakeTransport, ok, xlsx_bytes
from coordination.capture import capture_source
from coordination.sources import capture_all
from coordination.transport import HttpResponse
from coordination.util import sha256_bytes


def test_rejected_plain_request_is_kept_and_browser_retry_recorded(tmp_path, config, sources, fixture_bytes):
    src = sources["SRC-TICC-HALL"]
    url = src["retrieval"]["request_url"]
    rejected = fixture_bytes("rejected.html")
    page = "<html><title>x</title><body>大會堂 3122</body></html>".encode()
    t = FakeTransport({url: [ok(rejected, "text/html"), ok(page, "text/html")]})
    cap = capture_source(src, config.http_profiles, t, tmp_path)

    assert [a.profile for a in cap.attempts] == ["plain", "browser-like"]
    first, second = cap.attempts
    assert first.outcome == "rejected" and "Request Rejected" in first.reason
    assert (tmp_path / first.local_reference).read_bytes() == rejected
    assert first.sha256 == sha256_bytes(rejected)
    assert "User-Agent" not in first.request_headers
    assert t.requests[1].headers["User-Agent"].startswith("Mozilla/5.0")
    assert second.outcome == "retrieved" and cap.retrieval_status == "retrieved"
    assert cap.accepted is second


def test_no_browser_retry_when_plain_succeeds(tmp_path, config, sources):
    src = sources["SRC-TICC-HALL"]
    t = FakeTransport({src["retrieval"]["request_url"]: [ok("大會堂 3122".encode(), "text/html")]})
    cap = capture_source(src, config.http_profiles, t, tmp_path)
    assert len(cap.attempts) == 1 and len(t.requests) == 1


def test_no_retry_after_network_error_and_status_unavailable(tmp_path, config, sources):
    src = sources["SRC-TICC-4F"]
    cap = capture_source(src, config.http_profiles, FakeTransport({}), tmp_path)
    assert [a.outcome for a in cap.attempts] == ["network-error"]
    assert cap.retrieval_status == "unavailable" and cap.attempts[0].local_reference is None


def test_both_attempts_rejected_is_unavailable(tmp_path, config, sources, fixture_bytes):
    src = sources["SRC-TICC-ACCESS"]
    rej = ok(fixture_bytes("rejected.html"), "text/html")
    cap = capture_source(src, config.http_profiles,
                         FakeTransport({src["retrieval"]["request_url"]: [rej, rej]}), tmp_path)
    assert [a.outcome for a in cap.attempts] == ["rejected", "rejected"]
    assert cap.retrieval_status == "unavailable"


def test_sign_in_page_instead_of_workbook_is_invalid(tmp_path, config, sources):
    src = sources["SRC-BUDGET"]
    t = FakeTransport({src["retrieval"]["request_url"]: [ok(b"<html>Sign in</html>", "text/html")]})
    cap = capture_source(src, config.http_profiles, t, tmp_path)
    assert cap.retrieval_status == "invalid" and cap.attempts[0].local_reference.endswith(".html")


def test_http_403_is_rejected(tmp_path, config, sources):
    src = sources["SRC-TICC-4F"]
    url = src["retrieval"]["request_url"]
    t = FakeTransport({url: [HttpResponse(403, {}, b"denied", url), ok(b"%PDF-1.4 x", "application/pdf")]})
    cap = capture_source(src, config.http_profiles, t, tmp_path)
    assert [a.outcome for a in cap.attempts] == ["rejected", "retrieved"]


def test_notion_truncation_is_invalid(tmp_path, config, sources, notion_fixture):
    src = sources["SRC-BRIEF"]
    data = dict(notion_fixture)
    data["recordMap"] = {"block": {src["retrieval"]["notion_page_id"]: {"value": {"type": "page"}}}}
    data["cursor"] = {"stack": [["more"]]}
    t = FakeTransport({src["retrieval"]["request_url"]: [ok(json.dumps(data).encode(), "application/json")]})
    cap = capture_source(src, config.http_profiles, t, tmp_path)
    assert cap.retrieval_status == "invalid" and "truncated" in cap.attempts[0].reason
    assert t.requests[0].method == "POST"


def test_capture_all_records_every_source_and_withholds_failed_ones(tmp_path, config, sources):
    vend = sources["SRC-VENDOR"]
    hdr = list(vend["table"]["fields"])
    row = ["Q-1", "V", "venue", "pkg", 1, 1, "2026-10-17", "2026-09-05", "held", ""]
    t = FakeTransport({vend["retrieval"]["request_url"]: [ok(xlsx_bytes([hdr, row], "Vendor Quotes"))]})
    results = capture_all([vend, sources["SRC-TICC-4F"]], config.http_profiles, t, tmp_path)

    v = results["SRC-VENDOR"].record
    assert v["retrieval_status"] == "retrieved"
    assert v["observations"][0]["id"] == "OBS-SRC-VENDOR-Q-1"
    assert v["version_metadata"]["version_basis"] == "retrieval_timestamp"
    assert v["content_hash"].startswith("sha256:") and v["evidence_ids"][0] == "ATT-SRC-VENDOR-1"

    f = results["SRC-TICC-4F"].record
    assert f["retrieval_status"] == "unavailable"
    assert f["content_hash"] is None and f["local_reference"] is None and f["observations"] == []
    assert len(f["attempts"]) == 1


def test_parse_failure_marks_source_invalid(tmp_path, config, sources):
    src = sources["SRC-BRIEF"]
    page_id = src["retrieval"]["notion_page_id"]
    bad = {"cursor": {"stack": []}, "recordMap": {"block": {page_id: "not-a-dict"}}}
    t = FakeTransport({src["retrieval"]["request_url"]: [ok(json.dumps(bad).encode())]})
    rec = capture_all([src], config.http_profiles, t, tmp_path)["SRC-BRIEF"].record
    assert rec["retrieval_status"] == "invalid"
    assert rec["parse_issues"][0]["kind"] == "table-parse-failure"
