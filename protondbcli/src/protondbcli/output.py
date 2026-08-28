"""Terminal output formatting — the Tux banner + the verdict table.

Kept dependency-free (stdlib only, ground rule #2): no invented libs.
ANSI colors are emitted only when the terminal supports them.
"""

from __future__ import annotations

import os
import sys

from .api import GameResult, tier_icon
from .tux import tux_banner

# Tier → one-line verdict phrase (plain English, beginner-friendly)
TIER_VERDICT = {
    "platinum": "runs great out of the box",
    "gold": "runs well with minor tweaks",
    "silver": "runs, but needs patience and tweaks",
    "bronze": "runs poorly — expect problems",
    "borked": "does NOT run — do not buy for Linux yet",
    "pending": "not enough reports yet",
}


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def _c(text: str, code: str, enabled: bool) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if enabled else text


def _line(width: int, char: str = "─") -> str:
    return char * width


def render_result(result: GameResult, show_banner: bool = True) -> str:
    """Render the full answer: banner + verdict + fixes + how-to-run."""
    color = _supports_color()
    lines: list[str] = []

    if show_banner:
        lines.append(tux_banner(color=color))
        lines.append("")

    icon = tier_icon(result.tier)
    verdict = TIER_VERDICT.get(result.tier, "unknown tier")
    src = "cached" if result.source == "cache" else "live"
    confidence = result.confidence
    total = result.total_reports

    # The verdict box
    title = f" {icon} {result.name.upper()} "
    box_w = max(len(title) + 4, 56)
    lines.append("┌" + _line(box_w, "─") + "┐")
    lines.append("│" + title.ljust(box_w) + "│")
    lines.append("│" + _line(box_w, " ") + "│")
    verdict_line = f"  {verdict}"
    lines.append("│" + verdict_line.ljust(box_w) + "│")
    meta_line = f"  {total} community reports · {confidence} confidence · {src}"
    lines.append("│" + meta_line.ljust(box_w) + "│")
    lines.append("└" + _line(box_w, "─") + "┘")
    lines.append("")

    # The confirmed fixes (community-sourced, from the real report counts)
    lines.append(_c("✅ CONFIRMED FIXES (community-reports):", "1", color))
    fixes = _suggested_fixes(result)
    if fixes:
        for fix in fixes:
            lines.append(f"  • {fix}")
    else:
        lines.append("  • no fixes reported yet — check ProtonDB for the latest")
    lines.append("")

    # The how-to-run (new-to-Linux friendly)
    lines.append(_c("🚀 HOW TO RUN (new to Linux?):", "1", color))
    lines.append("  1. Open Steam")
    lines.append("  2. Find the game in your library")
    lines.append("  3. Right-click it → Properties")
    lines.append('  4. Click "Compatibility" on the left')
    lines.append('  5. Tick "Force the use of a specific Steam Play tool"')
    lines.append('  6. Pick "Proton 9.0" (or GE-Proton if you have it)')
    lines.append("  7. Back in Properties → Launch Options → paste this:")
    lines.append("       gamemoderun %command%")
    lines.append("  8. Click Play!")
    lines.append("")
    lines.append(_c(f"  Tip: check https://www.protondb.com/app/{result.appid} for the latest reports", "2", color))

    return "\n".join(lines)


def _suggested_fixes(result: GameResult) -> list[str]:
    """Plain-English fixes based on the real tier data (never invented)."""
    fixes: list[str] = []
    if result.tier in ("platinum", "gold"):
        fixes.append("Force Proton 9.0 (or GE-Proton) in Steam → Properties → Compatibility")
        fixes.append("Add gamemoderun %command% to the launch options for the CPU-governor boost")
    if result.tier == "silver":
        fixes.append("Check ProtonDB for the specific tweaks — Silver usually needs one extra step")
        fixes.append("Try GE-Proton instead of the default Proton (community-favourite)")
    if result.tier in ("bronze", "borked"):
        fixes.append("Try GE-Proton — community builds often fix what the default cannot")
        fixes.append("Check ProtonDB for the workaround before buying — save yourself the pain")
    if result.tier == "platinum":
        fixes.append("If you see stutter, enable FSR/upscaling in-game — big free FPS on AMD")
    return fixes
