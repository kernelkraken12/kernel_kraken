"""The `shaderwarm` command — the kernel kraken's shader cache keeper.

Usage:
    shaderwarm scan               list all games + their cache warmth
    shaderwarm status <game>      one game's cache state
    shaderwarm warm <game>        orchestrate a warmup pass (launches the game)
    shaderwarm warm <game> --watch   watch the cache grow while you play
    shaderwarm backup <game>      tar the cache to the XDG data dir
    shaderwarm clear <game> --yes remove the cache (confirmation required)
    shaderwarm --json             scriptable output (scan/status)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .cache import backup, clear, inspect
from .output import render_scan, render_status
from .steam import find_steam_root, scan_games, SteamGame


def _resolve_game(games: list[SteamGame], query: str) -> SteamGame | None:
    q = query.strip().lower()
    for g in games:
        if g.name.lower() == q or g.name.lower().startswith(q) or str(g.appid) == q:
            return g
    return None


def _xdg_data() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "shaderwarm" / "backups"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shaderwarm",
        description="The kernel kraken's shader cache keeper — warm shaders, smooth FPS.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="list all Steam games + cache warmth")
    p_scan.add_argument("--json", action="store_true", help="scriptable JSON output")
    p_status = sub.add_parser("status", help="show one game's cache state")
    p_status.add_argument("game")
    p_status.add_argument("--json", action="store_true", help="scriptable JSON output")
    p_warm = sub.add_parser("warm", help="launch a game so its shaders compile")
    p_warm.add_argument("game")
    p_warm.add_argument("--watch", action="store_true", help="poll the cache while you play")
    p_warm.add_argument("--interval", type=int, default=5)
    p_warm.add_argument("--rounds", type=int, default=60)
    p_backup = sub.add_parser("backup", help="tar a game's cache to the XDG data dir")
    p_backup.add_argument("game")
    p_clear = sub.add_parser("clear", help="remove a game's cache (needs --yes)")
    p_clear.add_argument("game")
    p_clear.add_argument("--yes", action="store_true", help="confirm the deletion")
    parser.add_argument("--version", action="version", version=f"shaderwarm {__version__}")
    args = parser.parse_args(argv)

    root = find_steam_root()
    if root is None:
        print("✗ Steam root not found — is Steam installed? (or set $STEAM_ROOT)", file=sys.stderr)
        return 1
    games = scan_games(root)

    if args.cmd == "scan":
        infos = {g.appid: inspect(g) for g in games}
        if args.json:
            payload = {
                str(g.appid): {
                    "name": g.name,
                    "appid": g.appid,
                    "state": infos[g.appid].state,
                    "size_bytes": infos[g.appid].size_bytes,
                    "file_count": infos[g.appid].file_count,
                    "newest_mtime": infos[g.appid].newest_mtime,
                    "exists": infos[g.appid].exists,
                }
                for g in games
            }
            print(json.dumps(payload, indent=2))
            return 0
        print(render_scan(games, infos))
        return 0
    game = _resolve_game(games, args.game)
    if game is None:
        print(f"✗ no game matching '{args.game}' — try: shaderwarm scan", file=sys.stderr)
        return 1

    if args.cmd == "status":
        info = inspect(game)
        if args.json:
            print(json.dumps({
                "name": game.name,
                "appid": game.appid,
                "state": info.state,
                "size_bytes": info.size_bytes,
                "file_count": info.file_count,
                "newest_mtime": info.newest_mtime,
                "exists": info.exists,
            }, indent=2))
            return 0
        print(render_status(info))
        return 0

    if args.cmd == "warm":
        from .warm import warm
        warm(game, watch=args.watch, interval=args.interval, rounds=args.rounds)
        return 0

    if args.cmd == "backup":
        dest = backup(game, _xdg_data())
        if dest is None:
            print(f"  no cache for {game.name} — nothing to back up")
            return 0
        print(f"  ✅ backed up {game.name}'s cache → {dest}")
        return 0

    if args.cmd == "clear":
        if not args.yes:
            print(f"  ⚠️ this will delete {game.name}'s shader cache ({game.root / 'steamapps' / 'shadercache' / str(game.appid)})")
            print("  re-run with --yes to confirm")
            return 1
        if clear(game):
            print(f"  ✅ cleared {game.name}'s shader cache (it will rebuild on next play)")
        else:
            print(f"  no cache for {game.name} — nothing to clear")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
