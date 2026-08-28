"""Local cache for query results — the fast repeat-answers + the 24h freshness.

XDG-compliant (ground rule #1): cache lives in ~/.cache/protondbcli/.
No hard-coded absolute paths.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

CACHE_DIR_ENV = "XDG_CACHE_HOME"
DEFAULT_TTL = 24 * 3600  # 24 hours


def cache_dir() -> Path:
    base = os.environ.get(CACHE_DIR_ENV) or str(Path.home() / ".cache")
    d = Path(base) / "protondbcli"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_path(appid: int) -> Path:
    return cache_dir() / f"{appid}.json"


def read_cache(appid: int, ttl: int = DEFAULT_TTL) -> dict | None:
    """Return the cached summary if fresh, else None."""
    path = _cache_path(appid)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    ts = data.get("_fetched_at", 0)
    if time.time() - ts > ttl:
        return None
    return data.get("summary")


def write_cache(appid: int, summary: dict) -> None:
    """Store a summary with a fetch timestamp."""
    payload = {"_fetched_at": time.time(), "summary": summary}
    try:
        _cache_path(appid).write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        # cache write failures are non-fatal — the answer still shows
        pass
