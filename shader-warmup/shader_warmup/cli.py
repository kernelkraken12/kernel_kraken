#!/usr/bin/env python3
"""shader-warmup — pre-bake DXVK shader caches so games start smooth.

Usage:
    shader-warmup "Cairn"
    shader-warmup --appid 1588550
    shader-warmup "Cairn" --check   # is it already warm?
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

APP_NAME = "shader-warmup"
__version__ = "0.1.0"

# Canonical Steam compatdata location
STEAM_HOME = Path("~/.steam/steam/steamapps/compatdata").expanduser()
DXVK_CACHE_SUFFIXES = (".dxvk-cache", ".dxvk-cache.v2")
WARMUP_SECONDS = 90


def find_game_dir(game: str) -> Path | None:
    """Locate a game's compatdata directory by name."""
    if not STEAM_HOME.is_dir():
        return None
    for entry in sorted(STEAM_HOME.iterdir()):
        if not entry.is_dir():
            continue
        marker = entry / "appinfo" / "appid"
        if not marker.is_file():
            continue
        try:
            appid = marker.read_text().strip()
        except OSError:
            continue
        # The compatdata dir is usually named by appid; find the one
        # whose appinfo matches. Fall back to a name search below.
        if appid:
            info = _appinfo_name(appid)
            if game.lower() in (info or "").lower():
                return entry
    # Fallback: search appinfo files for the name
    for entry in sorted(STEAM_HOME.iterdir()):
        info = _appinfo_name(entry.name)
        if game.lower() in (info or "").lower():
            return entry
    return None


def _appinfo_name(appid: str) -> str | None:
    """Best-effort game name from Steam's appinfo cache."""
    try:
        import configparser

        path = STEAM_HOME / appid / "appinfo" / "appid"
        if path.is_file():
            cfg = configparser.ConfigParser()
            cfg.read(path)
            return cfg.get("appinfo", "name", fallback=None)
    except Exception:
        pass
    return None


def shader_files(compatdir: Path) -> list[Path]:
    """All DXVK shader cache files inside a compatdata dir."""
    return [
        p
        for p in compatdir.rglob("*")
        if any(s in p.name for s in DXVK_CACHE_SUFFIXES)
    ]


def cache_size(compatdir: Path) -> int:
    return sum(p.stat().st_size for p in shader_files(compatdir))


def is_warm(compatdir: Path, min_bytes: int = 1024 * 1024) -> bool:
    """A cache counts as warm once it has grown past a threshold."""
    return cache_size(compatdir) >= min_bytes


def warm_up(compatdir: Path, appid: str | None, seconds: int = WARMUP_SECONDS) -> dict:
    """Warm a game by launching it briefly headless."""
    before = cache_size(compatdir)
    steam = shutil.which("steam")
    cmd: list[str] = []
    if steam and appid:
        cmd = [steam, "-applaunch", appid, "-windowed", "-nologo"]
    elif appid:
        cmd = ["steam", "-applaunch", appid, "-windowed", "-nologo"]

    if not cmd:
        return {
            "ok": False,
            "reason": "steam not found (install Steam or pass --appid)",
        }

    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "DXVK_STATE_CACHE_PATH": str(compatdir)},
        )
        time.sleep(seconds)
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    after = cache_size(compatdir)
    return {
        "ok": after > before,
        "before_bytes": before,
        "after_bytes": after,
        "baked_bytes": max(0, after - before),
        "elapsed_seconds": seconds,
    }


def render(result: dict, game: str, warm: bool) -> str:
    lines = [
        "   _  _  ____  ____  _  _  ____ ",
        "  ( \\( )(  _ \\(  _ \\( \\/ )(  _ \\",
        "   )  (  ) __/ ) __/ )  (  ) __/",
        "  (_)\\_)(__)  (__)  (_/\\_)(__)  ",
        "",
        f"🔥 shader-warmup — {game}",
    ]
    if warm:
        lines.append("✅ Already warm — launch and play smooth!")
        return "\n".join(lines) + "\n"
    if result.get("ok"):
        lines.append(
            f"✅ Warmed up! +{result['baked_bytes'] / 1024 / 1024:.1f} MB "
            f"of shaders baked in {result['elapsed_seconds']}s."
        )
    else:
        lines.append(f"⚠️ {result.get('reason', 'could not warm up')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Pre-bake DXVK shader caches so games start smooth.",
    )
    ap.add_argument("game", nargs="?", help="game name (case-insensitive)")
    ap.add_argument("--appid", help="Steam app id (skips name search)")
    ap.add_argument("--check", action="store_true", help="report warm/cold status")
    ap.add_argument("--seconds", type=int, default=WARMUP_SECONDS)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    args = ap.parse_args(argv)

    if not args.game and not args.appid:
        ap.error("provide a game name or --appid")

    compatdir = None
    if args.appid:
        compatdir = STEAM_HOME / args.appid
    elif args.game:
        compatdir = find_game_dir(args.game)

    if compatdir is None or not compatdir.is_dir():
        out = {
            "ok": False,
            "reason": f"compatdata for {args.game or args.appid} not found",
        }
        if args.json:
            print(json.dumps(out))
        else:
            print(out["reason"])
        return 1

    warm = is_warm(compatdir)
    result = {"ok": warm, "reason": "already warm"} if warm else warm_up(compatdir, args.appid, args.seconds)

    if args.json:
        print(json.dumps({**result, "game": args.game or args.appid, "warm": warm}))
    else:
        print(render(result, args.game or args.appid, warm))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
