"""Steam discovery: locate game names/appids from the local Steam install."""

from __future__ import annotations

import os
import re
import glob
from pathlib import Path

ACF_KEY = re.compile(r'^\s*"([^"]+)"\s+"([^"]*)"\s*$')
ACF_BLOCK = re.compile(r'^\s*"([^"]+)"\s*$')
STEAM_DIRS = [
    "~/.steam/steam",
    "~/.local/share/Steam",
    "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",
]


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


def find_steam_dirs() -> list[Path]:
    """Return the Steam root dirs that actually exist."""
    found: list[Path] = []
    for d in STEAM_DIRS:
        p = _expand(d)
        if p.is_dir():
            found.append(p)
    return found


def parse_acf(text: str) -> dict:
    """Parse a Valve KeyValues ACF file into a nested dict (naive but real)."""
    result: dict = {}
    stack: list[dict] = [result]
    current_key: str | None = None
    for line in text.splitlines():
        m = ACF_KEY.match(line)
        if m:
            key, value = m.group(1), m.group(2)
            if value == "":
                new: dict = {}
                stack[-1][key] = new
                stack.append(new)
            else:
                stack[-1][key] = value
            current_key = key
            continue
        m = ACF_BLOCK.match(line)
        if m and line.strip().endswith('"') and not line.strip().endswith('"}'):
            # a bare block key like "AppState" (the opening brace follows)
            key = m.group(1)
            new: dict = {}
            stack[-1][key] = new
            stack.append(new)
            current_key = key
            continue
        if line.strip() == "}":
            if len(stack) > 1:
                stack.pop()
    return result


def library_folders(steam_root: Path) -> list[Path]:
    """Read libraryfolders.vdf and return the library paths."""
    vdf = steam_root / "steamapps" / "libraryfolders.vdf"
    if not vdf.exists():
        return [steam_root / "steamapps"]
    folders: list[Path] = []
    try:
        data = parse_acf(vdf.read_text(encoding="utf-8", errors="replace"))
        lib = data.get("libraryfolders", {})
        for key, value in lib.items():
            if isinstance(value, dict):
                path = value.get("path")
                if path:
                    folders.append(Path(str(path)) / "steamapps")
            elif isinstance(value, str) and key.isdigit():
                folders.append(Path(value) / "steamapps")
    except Exception:
        pass
    return folders or [steam_root / "steamapps"]


def find_appid(name: str) -> int | None:
    """Find a Steam appid by (case-insensitive) game-name substring."""
    needle = name.strip().lower()
    if needle.isdigit():
        return int(needle)
    for root in find_steam_dirs():
        for folder in library_folders(root):
            for acf in sorted(glob.glob(str(folder / "appmanifest_*.acf"))):
                try:
                    data = parse_acf(Path(acf).read_text(encoding="utf-8", errors="replace"))
                    app = data.get("AppState", {})
                    appname = str(app.get("name", ""))
                    if needle in appname.lower():
                        try:
                            return int(app.get("appid", 0))
                        except (TypeError, ValueError):
                            continue
                except Exception:
                    continue
    return None


def appid_name(appid: int) -> str | None:
    """Resolve a real game name for an appid from the local manifests."""
    for root in find_steam_dirs():
        for folder in library_folders(root):
            acf = folder / f"appmanifest_{appid}.acf"
            if acf.exists():
                try:
                    data = parse_acf(acf.read_text(encoding="utf-8", errors="replace"))
                    name = data.get("AppState", {}).get("name")
                    if name:
                        return str(name)
                except Exception:
                    return None
    return None


def shader_cache_dir(appid: int) -> Path | None:
    """Return the shader cache dir for an appid, if any."""
    for root in find_steam_dirs():
        p = root / "steamapps" / "shadercache" / str(appid)
        if p.is_dir():
            return p
    return None


def shader_cache_size(appid: int) -> int:
    """Total bytes in the shader cache for an appid."""
    d = shader_cache_dir(appid)
    if not d:
        return 0
    total = 0
    for p in d.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            continue
    return total
