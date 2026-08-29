"""Shader-cache inspection: size, warmth, backup, clear.

The cache dir is the real `steamapps/shadercache/<appid>/`; the
DXVK / vkd3d-proton state caches are the files inside it. Size is
the honest proxy for "warmth": a big recent cache = shaders
already compiled; a missing/empty one = cold.
"""

from __future__ import annotations

import shutil
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path

from .steam import SteamGame, shader_cache_dir

# Real cache file patterns (DXVK + vkd3d-proton)
CACHE_PATTERNS = ("*.dxvk-cache", "*.vkd3d-proton.cache", "*.dxvk-cache.tmp")


@dataclass
class CacheInfo:
    game: SteamGame
    exists: bool
    size_bytes: int
    file_count: int
    newest_mtime: float
    state: str  # cold | cold-ish | warming | warm


def _dir_size(path: Path) -> tuple[int, int]:
    total = 0
    count = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
            count += 1
    return total, count


def _newest_mtime(path: Path) -> float:
    newest = 0.0
    for p in path.rglob("*"):
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
    return newest


def inspect(game: SteamGame) -> CacheInfo:
    """Measure a game's shader cache and classify its warmth."""
    d = shader_cache_dir(game)
    if not d.is_dir():
        return CacheInfo(game=game, exists=False, size_bytes=0, file_count=0, newest_mtime=0.0, state="cold")
    size, count = _dir_size(d)
    newest = _newest_mtime(d)
    if count == 0:
        state = "cold"
    elif size < 2_000_000:
        state = "cold-ish"
    else:
        age_hours = (time.time() - newest) / 3600
        state = "warm" if age_hours < 24 * 30 else "warming"
    return CacheInfo(game=game, exists=True, size_bytes=size, file_count=count, newest_mtime=newest, state=state)


def backup(game: SteamGame, dest: Path) -> Path | None:
    """Tar the cache dir into dest (the XDG data dir by default)."""
    d = shader_cache_dir(game)
    if not d.is_dir():
        return None
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"{game.appid}-{game.name.replace(' ', '-')[:30]}-{int(time.time())}.tar.gz"
    with tarfile.open(out, "w:gz") as tf:
        tf.add(d, arcname=f"shadercache-{game.appid}")
    return out


def clear(game: SteamGame) -> bool:
    """Remove the game's shader cache dir (caller must confirm)."""
    d = shader_cache_dir(game)
    if not d.is_dir():
        return False
    shutil.rmtree(d, ignore_errors=True)
    return True
