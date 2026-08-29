"""Steam discovery — real paths, real formats (ground rule #2).

Reads the actual Valve KeyValue formats:
- appmanifest_<appid>.acf  ->  game name per appid
- libraryfolders.vdf       ->  the extra library roots
The shader caches live in <library>/steamapps/shadercache/<appid>/.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

# The known real Steam roots on Linux (checked in order)
STEAM_ROOTS = (
    "~/.local/share/Steam",
    "~/.steam/steam",
    "~/snap/steam/common/.local/share/Steam",
    "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",
)


@dataclass
class SteamGame:
    appid: int
    name: str
    root: Path  # the library root that holds this game's appmanifest


def find_steam_root(override: str | None = None) -> Path | None:
    """Locate the primary Steam root (or use $STEAM_ROOT for testing)."""
    if override:
        p = Path(override).expanduser()
        return p if p.is_dir() else None
    env = os.environ.get("STEAM_ROOT")
    if env:
        p = Path(env).expanduser()
        if p.is_dir():
            return p
    for root in STEAM_ROOTS:
        p = Path(root).expanduser()
        if (p / "steamapps").is_dir():
            return p
    return None


def _parse_acf_name(text: str) -> str | None:
    """Extract the game name from an appmanifest .acf (real Valve KeyValue)."""
    m = re.search(r'"name"\s+"([^"]+)"', text)
    return m.group(1) if m else None


def library_roots(steam_root: Path) -> list[Path]:
    """Return all library roots: the primary + any in libraryfolders.vdf."""
    roots = [steam_root]
    vdf = steam_root / "steamapps" / "libraryfolders.vdf"
    if vdf.exists():
        try:
            text = vdf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        # the real format: "0" { "path" ".../SteamLibrary" ... }
        for m in re.finditer(r'"\d+"\s*\{[^}]*?"path"\s*"([^"]+)"', text):
            p = Path(m.group(1)).expanduser()
            if p.is_dir() and p not in roots:
                roots.append(p)
    return roots


def scan_games(steam_root: Path) -> list[SteamGame]:
    """Walk every library's steamapps for appmanifest_*.acf files."""
    games: dict[int, SteamGame] = {}
    for lib in library_roots(steam_root):
        steamapps = lib / "steamapps"
        if not steamapps.is_dir():
            continue
        for acf in steamapps.glob("appmanifest_*.acf"):
            m = re.match(r"appmanifest_(\d+)\.acf$", acf.name)
            if not m:
                continue
            appid = int(m.group(1))
            try:
                name = _parse_acf_name(acf.read_text(encoding="utf-8", errors="replace")) or f"app {appid}"
            except OSError:
                name = f"app {appid}"
            games.setdefault(appid, SteamGame(appid=appid, name=name, root=lib))
    return sorted(games.values(), key=lambda g: g.name.lower())


def shader_cache_dir(game: SteamGame) -> Path:
    """The real per-game shader cache dir (DXVK/vkd3d state caches live here)."""
    return game.root / "steamapps" / "shadercache" / str(game.appid)
