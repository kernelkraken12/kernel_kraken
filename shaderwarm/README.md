# 🐧 shaderwarm — the kernel kraken's shader cache keeper

**Warm shaders, smooth FPS. One command.**

A tiny terminal tool for Linux gamers. It scans Steam's real shader-cache
folders, tells you which games are "warm" (shaders already compiled — smooth
play) and which are cold (first-play stutter ahead), then helps you warm them
up before you actually play.

```
$ shaderwarm scan

      .--.
     |o_o |
     |:_/ |
    //   \ \
   (|     | )
  /'\_   _/`\
  \___)=(___/
  TUX WARMS THE PIPELINE: SHADERS READY?

  GAME                          STATE      CACHE     FILES
  ----------------------------------------------------------
  Cairn                          ✅ warm     32.1 MB       4
  Cyberpunk 2077                 🔥 warming  18.4 MB       2
  Some New Game                  ❄️ cold        —      —
```

## Why

On Proton, games translate their shaders (DX11/DX12 → Vulkan) **while you
play** — so the first time you enter a scene, the GPU compiles shaders on the
fly and the game stutters. The compiled shaders are cached to disk, so the
second run is smooth. **shaderwarm tells you when a game's cache is ready, and
orchestrates the warmup pass so you never hit first-play stutter again.**

For new Linux gamers: it explains in plain words. For everyone else: it's a
one-command cache manager (scan / warm / backup / clear).

## Install (works on EVERY Linux distro — no sudo, no package manager)

Python 3.10+ stdlib only — zero dependencies. Any of these work:

### Option 1 — the one-liner (easiest)
```bash
bash <(curl -fsSL https://kernelkraken12.github.io/kernel_kraken/shaderwarm/install.sh)
```
(once the repo is live; until then: `bash install.sh` from the project folder)

### Option 2 — pip
```bash
pip install --user shaderwarm    # or: pipx install shaderwarm
```

### Option 3 — manual
```bash
git clone https://github.com/kernelkraken12/kernel_kraken.git
cd kernel_kraken/shaderwarm
bash install.sh
```

Installs to `~/.local/bin/shaderwarm` — no root. If `~/.local/bin` isn't on
your PATH, the installer tells you the one line to add.

## Usage

```bash
shaderwarm scan                    # all games + cache warmth
shaderwarm status "cairn"          # one game's cache state (case-insensitive)
shaderwarm warm "cairn"            # launch the game so its shaders compile
shaderwarm warm "cairn" --watch    # watch the cache grow while you play
shaderwarm backup "cairn"          # tar the cache to ~/.local/share/shaderwarm/
shaderwarm clear "cairn" --yes     # remove the cache (confirmation required)
shaderwarm scan --json             # scriptable output
```

The tool finds Steam automatically (standard Linux install paths), or point it
at a custom Steam folder with `$STEAM_ROOT`.

## How it works

- **Real Steam paths**: reads `~/.local/share/Steam` (or the standard
  alternatives), parses the actual `libraryfolders.vdf` + `appmanifest_*.acf`
  files (Valve's real KeyValue format) to map games → libraries → appids.
- **Real cache dirs**: `steamapps/shadercache/<appid>/` — where DXVK /
  vkd3d-proton state caches live.
- **Honest warmth proxy**: a large, recent cache = shaders already compiled.
  Cold/missing = expect first-play stutter. The tool never pretends to compile
  shaders itself — the GPU does that; shaderwarm orchestrates the warmup pass
  and lets you watch the cache grow.
- **No invented data**: every path and format it reads is the real thing.

## Project layout (kernel_kraken standard)

```
shaderwarm/
├── src/shaderwarm/        # steam.py · cache.py · warm.py · output.py · cli.py
├── tests/                 # unittest suite (stdlib, fake Steam tree)
├── systemd/               # example unit + daily report timer
├── examples/              # sample output
├── Dockerfile
├── install.sh             # the distro-agnostic installer
├── pyproject.toml         # pip/pipx packaging
├── .gitignore
├── README.md
├── LICENSE                # MIT
└── CHECKLIST.md           # self-review: security, deps, edge cases, test steps
```

## Primary-repo notice

This project is part of the **Kernel Kraken** collection and lives at
[`kernelkraken12/kernel_kraken`](https://github.com/kernelkraken12/kernel_kraken)
on GitHub. It is mirrored there; the master copy lives in the family's
homelab archive.

## AI-assistance disclosure

This code was drafted with AI assistance and reviewed by a human before
release. All APIs, flags, and dependencies are real and verified.

## License

MIT — see [LICENSE](LICENSE). Built in the desert. Released by the kraken. 🐙
