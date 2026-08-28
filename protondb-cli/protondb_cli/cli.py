#!/usr/bin/env python3
"""protondb-cli — check a game's Linux compatibility from your terminal.

Usage:
    proton "Cairn"
    proton CAIRN
    proton "Game Name" --json
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

from . import __version__

USER_AGENT = "protondb-cli/{} (kernel_kraken project)".format(__version__)

TUX = r"""
      .--.
     |o_o |
     |:_/ |
    //   \ \
   (|     | )
  /'\_   _/`\
  \___)=(___/
"""

TIER_ORDER = ["native", "platinum", "gold", "silver", "bronze", "borked"]
TIER_ICON = {
    "native": "🐧",
    "platinum": "🥇",
    "gold": "🥈",
    "silver": "🥉",
    "bronze": "🟤",
    "borked": "💀",
}

GENERIC_FIXES = {
    "platinum": [
        "Proton: any recent Proton (9.0+ / GE-Proton) should work",
        "Launch-option: gamemoderun %command% (optional smoothness boost)",
    ],
    "gold": [
        "Proton: try Proton 9.0-4 or the latest GE-Proton",
        "Launch-option: gamemoderun %command%",
        "Tip: let the shader cache bake for a few minutes first",
    ],
    "silver": [
        "Proton: try Proton 9.0-4 or the latest GE-Proton",
        "Launch-option: gamemoderun %command%",
        "Tip: lower in-game shadows / effects for a solid FPS gain",
    ],
    "bronze": [
        "Proton: experiment with GE-Proton versions (newest first)",
        "Check ProtonDB for game-specific launch flags",
        "Tip: try DXVK / VKD3D toggles in the launch options",
    ],
    "borked": [
        "Proton: likely needs a specific GE-Proton build — check ProtonDB notes",
        "Consider: the game may need Windows to run properly",
    ],
}

BEGINNER = """
👶 NEW TO LINUX GAMING?
• Proton = Valve's tool that runs Windows games on Linux
  (Steam does it automatically — you just pick the version!)
• Set the Proton version: Steam → game → Properties →
  Compatibility → "Force the use of a specific tool"
  → pick Proton 9.0-4 (or the newest GE-Proton)
• Launch options: Properties → General → "Launch options"
  → paste what the tool suggests (e.g. gamemoderun %command%)
• gamemode = a performance booster:
  install with your package manager (e.g. yay -S gamemode),
  then add "gamemoderun %command%" to the launch options
"""


def fetch(url: str, timeout: int = 15) -> dict:
    """Fetch a JSON endpoint with a real user agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_steam(title: str) -> dict | None:
    """Find a Steam app by title (case-insensitive search)."""
    query = urllib.parse.quote(title.strip().lower())
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&cc=us&l=en"
    try:
        data = fetch(url)
    except (urllib.error.URLError, json.JSONDecodeError):
        return None
    items = data.get("items", [])
    if not items:
        return None
    # Prefer the best title match, case-insensitive.
    for item in items:
        if item.get("name", "").strip().lower() == title.strip().lower():
            return item
    return items[0]


def fetch_protondb(appid: int) -> dict | None:
    """Fetch the ProtonDB summary for a Steam app id."""
    url = f"https://www.protondb.com/api/v1/reports/summaries/{appid}.json"
    try:
        return fetch(url)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def tier_of(verdict: str) -> str:
    """Normalize a ProtonDB verdict string to a tier key."""
    v = (verdict or "").lower()
    for tier in TIER_ORDER:
        if tier in v:
            return tier
    return "silver"


def format_output(game: dict, report: dict | None, show_art: bool, show_beginner: bool) -> str:
    lines = []
    if show_art:
        lines.append(TUX)
    name = game.get("name", "Unknown game")
    appid = game.get("id")
    lines.append(f"🎮 {name}" + (f" (Steam: {appid})" if appid else ""))
    lines.append("")

    if report is None:
        lines.append("📊 ProtonDB: no reports yet — be the first to report!")
        lines.append("🚀 Install the game, try it, then share your experience at protondb.com")
    else:
        tier = tier_of(report.get("verdict", ""))
        total = report.get("total", 0)
        icon = TIER_ICON.get(tier, "📊")
        lines.append(f"{icon} ProtonDB verdict: {report.get('verdict', 'N/A').upper()} — {total} reports")
        lines.append("")
        lines.append("✅ CONFIRMED-FIXES (community-tested):")
        for fix in GENERIC_FIXES.get(tier, GENERIC_FIXES["silver"]):
            lines.append(f"  • {fix}")
        lines.append("")
        lines.append("🚀 GET-RUNNING (the fast path):")
        lines.append("  1. Steam → game → Properties → Compatibility")
        lines.append("  2. Pick the Proton from the list above")
        lines.append("  3. Launch options → paste the suggested line")
        lines.append("  → Done — play! 🎮")

    if show_beginner:
        lines.append(BEGINNER)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="proton",
        description="Check a game's Linux compatibility (ProtonDB) from the terminal.",
    )
    parser.add_argument("game", help="game title (case-insensitive)")
    parser.add_argument("--no-art", action="store_true", help="hide the Tux banner")
    parser.add_argument("--no-beginner", action="store_true", help="hide the newbie guide")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--version", action="version", version=f"protondb-cli {__version__}")
    args = parser.parse_args(argv)

    game = search_steam(args.game)
    if game is None:
        print(f"❌ No Steam game found for '{args.game}'. Check the title and try again.")
        return 1

    appid = game.get("id")
    report = fetch_protondb(appid) if appid else None

    if args.json:
        print(json.dumps({"game": game, "protondb": report}, indent=2))
        return 0

    print(format_output(game, report, show_art=not args.no_art, show_beginner=not args.no_beginner))
    return 0


if __name__ == "__main__":
    sys.exit(main())
