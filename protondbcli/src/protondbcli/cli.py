"""The `proton` command — the kernel kraken's game checker.

Usage:
    proton <game>          # "proton cairn" or "proton CAIRN" or "proton 1588550"
    proton <game> --fresh  # skip the cache, hit the live APIs
    proton <game> --json   # scriptable JSON output
    proton <game> --quiet  # no Tux banner (scripting)

Case-insensitive: the game title is normalized before the Steam search.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .api import APIError, appdetails_name, build_result, get_summary, search_steam
from .cache import read_cache, write_cache
from .output import render_result


def _normalize(query: str) -> str:
    """Lowercase + strip so 'CAIRN' / 'Cairn' / ' cairn ' all work."""
    return query.strip().lower()


def _lookup_appid(query: str) -> tuple[str, int] | None:
    """Resolve a game name to (name, appid). Accepts a bare appid too."""
    q = _normalize(query)
    if q.isdigit():
        # the user typed an appid directly — resolve the REAL name
        try:
            appid = int(q)
        except ValueError:
            return None
        try:
            real = appdetails_name(appid)
        except APIError:
            real = None
        return (real or q), appid
    results = search_steam(q)
    if not results:
        return None
    # prefer the first exact-ish match (the Steam search returns relevant hits)
    best = results[0]
    return best["name"], best["appid"]


def run(query: str, fresh: bool = False, quiet: bool = False) -> int:
    try:
        found = _lookup_appid(query)
    except APIError as e:
        print(f"✗ could not reach Steam search: {e}", file=sys.stderr)
        return 1
    if not found:
        print(f"✗ no game found for '{query}' — check the spelling or try the Steam appid", file=sys.stderr)
        return 1
    name, appid = found

    summary = None
    source = "live"
    if not fresh:
        summary = read_cache(appid)
        if summary is not None:
            source = "cache"
    if summary is None:
        try:
            summary = get_summary(appid)
            write_cache(appid, summary)
            source = "live"
        except APIError as e:
            print(f"✗ could not reach ProtonDB: {e}", file=sys.stderr)
            print("  try again later, or use --fresh once the network is back", file=sys.stderr)
            return 1

    result = build_result(appid, name, summary, source=source)

    if quiet:
        print(f"{result.name} [{result.appid}]: {result.tier} ({result.confidence}) — {result.total_reports} reports")
        return 0

    print(render_result(result, show_banner=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="proton",
        description="The kernel kraken's game checker — will it run on Linux, and how?",
    )
    parser.add_argument("game", help="game title (case-insensitive) or Steam appid, e.g. 'cairn' or 1588550")
    parser.add_argument("--fresh", action="store_true", help="skip the cache and fetch the latest from the live APIs")
    parser.add_argument("--json", dest="as_json", action="store_true", help="output JSON (scriptable)")
    parser.add_argument("--quiet", action="store_true", help="minimal one-line output, no Tux banner")
    parser.add_argument("--version", action="version", version=f"protondbcli {__version__}")
    args = parser.parse_args(argv)

    try:
        found = _lookup_appid(args.game)
    except APIError as e:
        print(f"✗ could not reach Steam search: {e}", file=sys.stderr)
        return 1
    if not found:
        print(f"✗ no game found for '{args.game}' — check the spelling or try the Steam appid", file=sys.stderr)
        return 1
    name, appid = found

    summary = None
    source = "live"
    if not args.fresh:
        summary = read_cache(appid)
        if summary is not None:
            source = "cache"
    if summary is None:
        try:
            summary = get_summary(appid)
            write_cache(appid, summary)
            source = "live"
        except APIError as e:
            print(f"✗ could not reach ProtonDB: {e}", file=sys.stderr)
            print("  try again later, or use --fresh once the network is back", file=sys.stderr)
            return 1

    result = build_result(appid, name, summary, source=source)

    if args.as_json:
        print(json.dumps({
            "name": result.name,
            "appid": result.appid,
            "tier": result.tier,
            "confidence": result.confidence,
            "score": result.score,
            "total_reports": result.total_reports,
            "trending_tier": result.trending_tier,
            "source": result.source,
        }, indent=2))
        return 0

    if args.quiet:
        print(f"{result.name} [{result.appid}]: {result.tier} ({result.confidence}) — {result.total_reports} reports")
        return 0

    print(render_result(result, show_banner=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
