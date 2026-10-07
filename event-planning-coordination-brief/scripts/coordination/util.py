"""Hashing, timestamps, canonical JSON and atomic writes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def utc_now() -> str:
    """Actual wall-clock time, used for retrieval and snapshot creation (never the business clock)."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def dumps(obj) -> bytes:
    """Canonical serialisation used for every JSON artifact, so hashes are reproducible."""
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def safe_id(text: str) -> str:
    """Make a value usable inside a record id (letters, digits, '-', '_', '.')."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(text)).strip("-") or "x"
