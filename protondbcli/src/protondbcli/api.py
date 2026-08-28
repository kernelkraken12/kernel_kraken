"""API client for the ProtonDB + Steam public APIs.

Real endpoints only (ground rule #2):
- Steam store search:  https://store.steampowered.com/api/storesearch/
- ProtonDB summaries: https://www.protondb.com/api/v1/reports/summaries/<appid>.json
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
PROTOND_BASE = "https://www.protondb.com/api/v1/reports/summaries/"

# Tier display order + labels (matching the real ProtonDB tiers)
TIERS = ["platinum", "gold", "silver", "bronze", "borked", "pending"]
TIER_ICONS = {
    "platinum": "🏆",
    "gold": "🥇",
    "silver": "🥈",
    "bronze": "🥉",
    "borked": "💀",
    "pending": "⏳",
}


class APIError(Exception):
    """Raised when a real API call fails (network, HTTP, or parse)."""


@dataclass
class GameResult:
    """The final answer for one game query."""

    name: str
    appid: int
    tier: str
    confidence: str
    score: float | None
    total_reports: int
    trending_tier: str | None
    source: str = "live"  # "live" or "cache"
    fetched_at: float = field(default_factory=time.time)


def _http_get_json(url: str, timeout: int = 20) -> dict:
    """Fetch a URL and parse JSON. Raises APIError on any real failure."""
    req = urllib.request.Request(url, headers={"User-Agent": "protondbcli/0.1 (kernel-kraken; Linux)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise APIError(f"HTTP {e.code} from {url}") from e
    except urllib.error.URLError as e:
        raise APIError(f"network error: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise APIError(f"bad JSON from {url}: {e}") from e


def search_steam(query: str, limit: int = 5) -> list[dict]:
    """Search the Steam store for a game by name. Returns [{name, appid, type}]."""
    params = urllib.parse.urlencode({"term": query, "cc": "US", "l": "en"})
    data = _http_get_json(f"{STEAM_SEARCH_URL}?{params}")
    items = data.get("items") or []
    out = []
    for item in items:
        name = item.get("name")
        appid = item.get("id")
        if name and appid:
            out.append({"name": name, "appid": int(appid), "type": item.get("type", "app")})
    return out[:limit]


def appdetails_name(appid: int) -> str | None:
    """Look up the real game name for an appid (Steam appdetails endpoint)."""
    params = urllib.parse.urlencode({"appids": appid, "cc": "US", "l": "en"})
    data = _http_get_json(f"{STEAM_APPDETAILS_URL}?{params}")
    entry = data.get(str(appid)) or {}
    if entry.get("success"):
        return entry.get("data", {}).get("name")
    return None


def get_summary(appid: int) -> dict:
    """Fetch the ProtonDB summary for an appid (real API)."""
    return _http_get_json(f"{PROTOND_BASE}{appid}.json")


def build_result(appid: int, name: str, summary: dict, source: str = "live") -> GameResult:
    """Map the real ProtonDB summary JSON onto the GameResult dataclass."""
    tier = str(summary.get("bestReportedTier") or summary.get("tier") or "pending").lower()
    if tier not in TIERS:
        tier = "pending"
    return GameResult(
        name=name,
        appid=appid,
        tier=tier,
        confidence=str(summary.get("confidence") or "unknown"),
        score=summary.get("score"),
        total_reports=int(summary.get("total") or 0),
        trending_tier=str(summary.get("trendingTier") or tier).lower(),
        source=source,
    )


def tier_icon(tier: str) -> str:
    return TIER_ICONS.get(tier, "❓")
