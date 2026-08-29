"""The warmup orchestration — the honest mechanics.

The GPU does the real compiling; this tool orchestrates:
1. Snapshot the cache size before launch.
2. Launch the game through the real Steam protocol
   (steam steam://rungameid/<appid>).
3. Tell the player to do a quick intro/first-scene pass.
4. (--watch) poll the cache size while the game runs so the
   player can SEE the shaders piling in.
"""

from __future__ import annotations

import subprocess
import time

from .cache import inspect
from .steam import SteamGame


def launch_steam(appid: int) -> None:
    """Launch a game via the real Steam URI protocol."""
    # steam steam://rungameid/<appid> is the standard external-launch route
    subprocess.Popen(["steam", f"steam://rungameid/{appid}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def warm(game: SteamGame, watch: bool = False, interval: int = 5, rounds: int = 60) -> None:
    """Orchestrate a warmup pass."""
    before = inspect(game)
    print(f"🐧 Warming up {game.name}...")
    print(f"   cache before: {before.state} ({before.size_bytes / 1_000_000:.1f} MB)")
    launch_steam(game.appid)
    print(f"   launched via steam://rungameid/{game.appid}")
    print("   ▶ play the intro / menu / first scene for a few minutes —")
    print("     that is what compiles the shaders.")
    if watch:
        print(f"   watching the cache every {interval}s (up to {rounds * interval}s)...")
        for i in range(rounds):
            time.sleep(interval)
            info = inspect(game)
            delta = info.size_bytes - before.size_bytes
            print(f"   [{i * interval + interval:>3}s] {info.state} — {info.size_bytes / 1_000_000:.1f} MB "
                  f"(+{delta / 1_000_000:.1f} MB this session)")
            if delta > 0 and info.state == "warm":
                print("   ✅ cache is warm — shaders compiled! Restart the game for a smooth run.")
                return
        print("   (watch window ended — run `shaderwarm status <game>` to re-check)")
    else:
        print("   afterwards run:  shaderwarm status <game>   to confirm it's warm.")
