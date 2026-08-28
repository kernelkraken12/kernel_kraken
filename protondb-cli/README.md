# 🎮 protondb-cli

**The Linux gamer's compatibility oracle — check any Steam game's Linux status from your terminal.**

> **Primary repository:** [kernel_kraken](https://github.com/kernelkraken12/kernel_kraken) · This project was built with AI assistance.

Type one command, get the verdict: does it run on Linux, what Proton to use, and the exact steps to get playing — fast.

## 🚀 Quick start

```bash
# Install (pick one)
uv tool install protondb-cli      # modern universal
pipx install protondb-cli         # classic
yay -S protondb-cli               # Arch / CachyOS (once packaged)

# Use it
proton "Cairn"        # case doesn't matter
proton CAIRN
```

## ✨ Features

- **One command** — `proton "Game Name"` (case-insensitive)
- **Live verdicts** — pulls the current ProtonDB rating (Native / Platinum / Gold / Silver / Bronze / Borked)
- **Confirmed fixes** — community-tested Proton versions, launch options, and tips
- **Fast path** — the exact 3 steps to get the game running
- **Newbie guide** — a built-in primer for people new to Linux gaming (hide with `--no-beginner`)
- **Tux banner** — the penguin greets you every run (hide with `--no-art`)
- **JSON output** — `--json` for scripting

## 📖 How it works

1. `proton "Cairn"` searches the Steam store (case-insensitive) and finds the app ID.
2. It queries the public ProtonDB API for the latest community verdict.
3. It prints the verdict, the confirmed fixes, and the fast path to playing.

## 🧪 Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest            # run the tests (no network needed)
python -m protondb_cli "Cairn"
```

## 🗂️ Project layout

```
protondb-cli/
├── protondb_cli/       # the CLI package
├── tests/              # unit tests (mocked, offline)
├── systemd/            # example cache-refresh timer
├── examples/           # sample output
├── Dockerfile
└── pyproject.toml
```

## 📜 License

MIT — free to use, modify, and share. The Kraken guards the kernel; the code is yours.
