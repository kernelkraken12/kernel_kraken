# 🧙♂️ Gamesage

**After a playthrough, turn your game session into a simple report + smart Linux performance tips.**

> **Primary repository:** [kernel_kraken](https://github.com/kernelkraken12/kernel_kraken) · **Built with AI assistance** (see below).

## The problem it solves
After gaming on Linux, players want to know *how it ran* and *how to make it run better* — without digging through logs. Gamesage reads your MangoHud session log and prints a plain-language report with a verdict, a simple health check, and copy-paste performance tips.

## Quick start
```bash
# Install (pick one)
uv tool install gamesage        # the modern universal
pipx install gamesage           # the classic

# After a playthrough:
gamesage "Cairn"

# Or the full stats for the nerds:
gamesage "Cairn" --detailed
```

## What it does
- Reads your **MangoHud session log** (enable logging with `MANGOHUD_CONFIG=log_interval=1000` in the launch options)
- Prints a **simple verdict**: 🟢 ran great / 🟡 could be better / 🔴 needs help
- Suggests **copy-paste tweaks** (GE-Proton, gamemode, FPS cap, shader-warmup, texture quality)
- **Saves every report** so you can look back at your past sessions

## Example output
```
🟢 Your game ran GREAT — smooth and happy!

💡 QUICK WINS:
  • Hot CPU — cap frames: add `MANGOHUD_CONFIG=fps_limit=60 %command%` to the launch options.

📄 Your report has been saved to: ~/.local/share/gamesage/Cairn/latest.txt
   (Come back any time — your past reports live here too.)
```

## Development
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pytest tests/ -q
```

## License
MIT

## AI assistance disclosure
This project was designed and built with the help of AI agents (the Kernel Kraken crew). The code is intentionally simple, dependency-free (Python stdlib only), and fully auditable.
