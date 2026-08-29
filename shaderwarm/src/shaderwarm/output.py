"""The Tux banner + the output formatting (stdlib-only, ANSI-aware)."""

from __future__ import annotations

import os
import sys

from .cache import CacheInfo
from .steam import SteamGame

# The canonical Tux (the family's pick — same as protondbcli)
TUX = r"""
      .--.
     |o_o |
     |:_/ |
    //   \ \
   (|     | )
  /'\_   _/`\
  \___)=(___/
"""

STATE_ICONS = {"cold": "❄️", "cold-ish": "🌤️", "warming": "🔥", "warm": "✅"}


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def banner() -> str:
    return TUX + "  TUX WARMS THE PIPELINE: SHADERS READY?\n"


def _mb(size: int) -> str:
    return f"{size / 1_000_000:.1f} MB"


def render_scan(games: list[SteamGame], infos: dict[int, CacheInfo]) -> str:
    lines = [banner(), ""]
    if not games:
        lines.append("  No Steam games found — is Steam installed, or set STEAM_ROOT?")
        return "\n".join(lines)
    lines.append("  GAME                          STATE      CACHE     FILES")
    lines.append("  " + "-" * 58)
    for g in games:
        info = infos[g.appid]
        icon = STATE_ICONS.get(info.state, "?")
        size = "—" if not info.exists else _mb(info.size_bytes)
        count = "—" if not info.exists else str(info.file_count)
        lines.append(f"  {g.name[:30]:<30} {icon} {info.state:<9} {size:>8} {count:>6}")
    lines.append("")
    lines.append("  ✅ warm = shaders compiled (smooth play)  ❄️ cold = never warmed")
    return "\n".join(lines)


def render_status(info: CacheInfo) -> str:
    icon = STATE_ICONS.get(info.state, "?")
    lines = [banner(), ""]
    lines.append(f"  {info.game.name} [{info.game.appid}]")
    lines.append(f"    state:  {icon} {info.state}")
    if info.exists:
        lines.append(f"    cache:  {_mb(info.size_bytes)} · {info.file_count} files")
        lines.append(f"    dir:    {info.game.root / 'steamapps' / 'shadercache' / str(info.game.appid)}")
    else:
        lines.append("    cache:  none yet — run `shaderwarm warm <game>` after playing a bit")
    lines.append("")
    if info.state == "warm":
        lines.append("  ✅ Smooth sailing — shaders are cached.")
    elif info.state in ("cold", "cold-ish"):
        lines.append("  ❄️  Cold cache — expect stutter on the first play, or warm it up first.")
    else:
        lines.append("  🔥 Cache is building — a recent session compiled shaders.")
    return "\n".join(lines)
