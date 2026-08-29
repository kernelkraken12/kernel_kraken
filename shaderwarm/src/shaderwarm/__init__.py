#!/usr/bin/env python3
"""shaderwarm — the kernel kraken's shader-warmup + cache keeper.

Scans Steam's real shader-cache dirs, tells you if a game is
"warm" (shaders compiled), orchestrates a warmup pass, and backs
up / clears per-game caches. Stdlib-only, works on every distro.
"""

__version__ = "0.1.0"
