import io
import json
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "event-planning-coordination-brief" / "scripts"))

from coordination.config import load_config, load_sources  # noqa: E402
from coordination.transport import HttpResponse  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def xlsx_bytes(rows, title="Sheet1", hidden_rows=(), hidden_cols=(), extra_sheets=()):
    wb = Workbook()
    ws = wb.active
    ws.title = title
    for row in rows:
        ws.append(row)
    for r in hidden_rows:
        ws.row_dimensions[r].hidden = True
    for c in hidden_cols:
        ws.column_dimensions[c].hidden = True
    for name, state in extra_sheets:
        s = wb.create_sheet(name)
        s.sheet_state = state
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class FakeTransport:
    """Returns queued responses per URL and records every request it receives."""

    def __init__(self, responses: dict):
        self.responses = {k: list(v) for k, v in responses.items()}
        self.requests = []

    def __call__(self, req):
        self.requests.append(req)
        queue = self.responses.get(req.url)
        if not queue:
            return HttpResponse(None, {}, b"", None, "no fake response queued")
        return queue.pop(0)


def ok(body: bytes, ctype="application/octet-stream"):
    return HttpResponse(200, {"content-type": ctype}, body, None)


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def sources():
    return {s["id"]: s for s in load_sources()}


@pytest.fixture
def fixture_bytes():
    return lambda name: (FIXTURES / name).read_bytes()


@pytest.fixture
def notion_fixture():
    return json.loads((FIXTURES / "notion-brief.json").read_text(encoding="utf-8"))
