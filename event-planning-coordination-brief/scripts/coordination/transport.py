"""HTTP transport. Kept behind a small interface so tests can inject a fake."""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: bytes | None = None


@dataclass(frozen=True)
class HttpResponse:
    status: int | None
    headers: dict
    body: bytes
    final_url: str | None
    error: str | None = None


Transport = Callable[[HttpRequest], HttpResponse]


def tls_context() -> ssl.SSLContext:
    """Full certificate-chain and hostname verification.

    Python 3.13 adds VERIFY_X509_STRICT by default, which rejects the TICC certificate chain because a
    certificate lacks a Subject Key Identifier extension. Only that strictness flag is cleared; chain
    trust and hostname checks stay on.
    """
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
    return ctx


def urllib_transport(timeout: float) -> Transport:
    ctx = tls_context()

    def send(req: HttpRequest) -> HttpResponse:
        r = urllib.request.Request(req.url, data=req.body, method=req.method, headers=dict(req.headers))
        try:
            with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
                return HttpResponse(resp.status, {k.lower(): v for k, v in resp.headers.items()},
                                    resp.read(), resp.geturl())
        except urllib.error.HTTPError as exc:
            body = exc.read() if exc.fp else b""
            return HttpResponse(exc.code, {k.lower(): v for k, v in (exc.headers or {}).items()},
                                body, req.url, f"HTTP {exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return HttpResponse(None, {}, b"", None, f"{type(exc).__name__}: {exc}")

    return send
