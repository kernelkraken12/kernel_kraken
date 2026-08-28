# 🐧 protondbcli — the kernel kraken's game checker

**Will it run on Linux — and how? One command, five seconds.**

A tiny terminal tool for Linux gamers (and Windows refugees who hate Windows).
Type a game name, get the community verdict from ProtonDB plus plain-English
fixes and exact setup steps.

```
$ proton cairn

      .--.
     |o_o |
     |:_/ |
    //   \ \
   (|     | )
  /'\_   _/`\
  \___)=(___/
  TUX APPROVES: WILL IT RUN ON LINUX?

  ┌─ 🏆 CAIRN ─────────────────────────┐
  │   runs great out of the box        │
  │   81 community reports · strong    │
  └────────────────────────────────────┘

  ✅ CONFIRMED FIXES (community-reports):
    • Force Proton 9.0 (or GE-Proton) ...
    • Add gamemoderun %command% ...
  🚀 HOW TO RUN (new to Linux?):
    1. Open Steam ...
    ...
```

## Why

- **New Linux gamers** get click-by-click instructions — no jargon, no forums.
- **Experienced gamers** get a 5-second "will it run / how" answer in the
  terminal — no browser, no ProtonDB tab hunting.
- **Hates-Windows gamers** get one less reason to ever touch Windows.

## Install (works on EVERY Linux distro — no sudo, no package manager)

The tool is **Python 3.10+ stdlib only** — zero dependencies — so it runs on
Fedora, Ubuntu/Debian, Arch, CachyOS, openSUSE, Alpine, NixOS (non-Nix path),
and anything else with Python 3. Any of these work:

### Option 1 — the one-liner (easiest)
```bash
bash <(curl -fsSL https://kernelkraken12.github.io/kernel_kraken/protondbcli/install.sh)
```
(once the repo is live; until then: `bash install.sh` from the project folder)

### Option 2 — pip
```bash
pip install --user protondbcli    # or: pipx install protondbcli
```

### Option 3 — manual
```bash
git clone https://github.com/kernelkraken12/kernel_kraken.git
cd kernel_kraken/protondbcli
bash install.sh
```

Installs to `~/.local/bin/proton` + `~/.local/lib/protondbcli/` — no root.
If `~/.local/bin` isn't on your PATH, the installer tells you the one line to add.

## Usage

```bash
proton cairn              # case-insensitive: CAIRN, Cairn, cairn all work
proton "elden ring"       # multi-word titles work
proton 1588550            # a Steam appid works too
proton cairn --fresh      # skip the cache, hit the live APIs now
proton cairn --json       # scriptable JSON output
proton cairn --quiet      # one-line output, no Tux banner
```

Results are cached in `~/.cache/protondbcli/` for 24 hours (repeat queries are
instant); `--fresh` bypasses the cache.

## How it works

- **Steam store search API** (`store.steampowered.com/api/storesearch`) resolves
  the name → Steam appid.
- **ProtonDB API** (`protondb.com/api/v1/reports/summaries/<appid>.json`) returns
  the community tier, confidence, and report count.
- The tier (platinum/gold/silver/bronze/borked/pending) maps to plain-English
  verdicts and beginner-friendly fixes. **No invented data** — everything shown
  comes from the real APIs or the tier mapping.

## Project layout (kernel_kraken standard)

```
protondbcli/
├── src/protondbcli/       # the package (api.py, cache.py, output.py, tux.py, cli.py)
├── tests/                 # unittest suite (stdlib)
├── systemd/               # example unit + daily cache-warm timer
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
