# gamesage — the Linux gamer's session sage 🐧

Turn a gaming session into a friendly report: how long you played, how hot the
GPU got, the FPS story, and — best of all — **plain-English performance tweaks**
tailored to what the session actually showed.

Made with 🧡 by the Kernel Kraken crew for Linux gamers.

## Why

Linux gaming is great, but "why is my FPS low?" usually means digging through
logs and forums. gamesage watches your session quietly, then tells you what
happened and what to try — in words a human can read, not a spreadsheet.

- **Friendly by default** — a verdict + simple tips (a `--detailed` view is on
  the roadmap).
- **Zero configuration** — no config file, no accounts, no telemetry.
- **Respects your machine** — reads local sensors only; nothing leaves your PC.
- **Works everywhere** — stdlib-only Python, no sudo, XDG paths.

## Install

Pick whichever is easiest:

**Option 1 — the one-liner (from this repo folder):**
```bash
bash install.sh
export PATH="$HOME/.local/bin:$PATH"   # one time, if the installer suggests it
```

**Option 2 — pip:**
```bash
pip install --user gamesage
```

**Option 3 — run without installing:**
```bash
python3 -m gamesage --help
```

Requires Python 3.10+ on any Linux distro. No root, no dependencies.

## Usage

The whole flow is three commands:

```bash
gamesage start "Cairn"      # 1. run BEFORE you launch the game
# ... play the game ...
gamesage end                # 2. after you finish — the report prints + saves
gamesage last               # 3. (any time) point at the latest report
```

The report is saved automatically after every playthrough as an HTML file in
`~/Documents/gaming-reports/` — open it in any browser to view it, share a
screenshot, or just keep it as your personal gaming diary.

> 💾 **The report saves itself** — after `gamesage end`, the HTML report is
> written to your gaming-reports folder and the terminal shows where.

### The report

```
  ┌────────────────────────────────────────────┐
  │  🐙 GAMESAGE — SESSION REPORT              │
  └────────────────────────────────────────────┘
  🎮 Game:        Cairn  [1588550]
  ⏱ Duration:    1h 12m
  🎭 Proton:      Proton 9.0-4
  🌡 Peak GPU:    67°C
  🧠 Peak CPU:    74%
  ⚡ FPS (MangoHud): avg 58.4 · min 31 · max 72
  📦 Shader-cache: 33.6MB
  ─────────────────────────────────────────────
  🧠 RECOMMENDATIONS:
    🟡 FPS is modest. FSR/upscaling or a small render-scale drop usually gains a clean 20–40%.
    🟢 Cairn is CPU-bound on Linux — try Proton-GE + `gamemoderun %command%`.
```

### The friendly touch

The report uses **plain words + emoji verdicts** — it tells you whether your
session was 🟢 smooth, 🟡 needs a tweak, or 🔴 running hot — then suggests
exactly what to try, in the order of biggest impact first.

### Watch mode (zero commands)

```bash
gamesage watch
```
Watches for a running Steam game, auto-starts the session when one launches,
and auto-reports when it closes. Perfect for a background systemd service.

### Other commands

| Command | What it does |
|---|---|
| `gamesage start "Game"` | start a session (run first!) |
| `gamesage end` | finish + save the report |
| `gamesage last` | show the latest report path |
| `gamesage report` | show the latest (or `--file <path>`) report |
| `gamesage watch` | auto-detect + auto-report |

## How it works

- **Session data** — a small background sampler reads the system sensors
  (`/sys/class/hwmon/*` temperatures, `/proc/loadavg` CPU) every ~20s during
  your session and stores them in `~/.local/state/gamesage/`.
- **FPS** — if MangoHud is installed, its log is parsed for the session's
  average/min/max FPS. No MangoHud? The report simply says so and suggests
  installing it (no magic numbers, ever).
- **Steam info** — game names/appids are read from your real local Steam
  manifests (`appmanifest_*.acf`), and the shader-cache size from
  `steamapps/shadercache/<appid>/`.
- **Recommendations** — a small, honest rules engine (real, common
  performance knowledge: temps, FPS, CPU load, shader cache) plus a few
  known per-game tips. Recommendations are **friendly guidelines**, never
  guarantees — the player stays the judge.

## Project layout

```
gamesage/
├── gamesage/
│   ├── __init__.py      # version
│   ├── cli.py           # the commands
│   ├── session.py       # session state + the background watcher
│   ├── monitor.py       # hwmon temps, CPU, MangoHud log
│   ├── steam.py         # Steam manifests, appids, shader cache
│   ├── rules.py         # the recommendations engine
│   └── report.py        # terminal + HTML report builders
├── tests/test_gamesage.py
├── systemd/gamesage.service
├── examples/sample-output.txt
├── install.sh
├── Dockerfile
├── pyproject.toml
├── CHECKLIST.md
├── LICENSE
└── README.md
```

## Development

```bash
python3 -m unittest discover -s tests -v
```

## ⚠️ AI-assistance disclosure

This project was drafted with AI assistance (the Kernel Kraken's sister agents)
and reviewed by a human (大哥) before release.

## 📦 Primary-repo mirror notice

This project lives in and is mirrored to the
[`kernelkraken12/kernel_kraken`](https://github.com/kernelkraken12/kernel_kraken)
repo on GitHub — the Kernel Kraken's lair of Linux-first open-source tools.

## License

MIT — do what you like, credit the Kraken crew. 🐙
