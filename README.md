# 🐙 Kernel Kraken

**The Kernel Kraken's lair — open-source software, Linux-first tools, and homelab experiments.**

A collection of practical, Linux-focused open-source projects: CLI utilities, TUI apps,
Proxmox/homelab scripts, and system helpers for the FOSS community. Every project in
this repo is tested before it is uploaded.

## 📦 Projects

| Project | What it does |
|---|---|
| [**protondb-cli**](protondb-cli/) | Check any Steam game's Linux compatibility (ProtonDB) from your terminal — verdicts, confirmed fixes, and beginner guidance. |
| [**shader-warmup**](shader-warmup/) | Pre-bake DXVK shader caches so Linux games start smooth — no more first-minute stutter. |
| [**gamesage**](gamesage/) | Session reports + performance tweaks for Linux gamers — run before you play, get a friendly report + tips after. |

## 🧰 What lives here

- CLI utilities and TUI apps for everyday Linux use
- Proxmox and homelab helpers
- Linux-gaming tools (Proton, DXVK, shader caches)
- System scripts and configuration examples
- Android open-source experiments (when they arrive)

## 📜 Project conventions

Every project follows the same canonical structure:

```
<project>/
├── src/
├── tests/
├── systemd/           # example units
├── examples/          # sample configs and outputs
├── android/           # only when Android code exists
├── Dockerfile
├── .gitignore
├── README.md          # primary-repo note + AI-assistance disclosure
├── LICENSE            # MIT
└── CHECKLIST.md       # security notes, deps, edge cases, test steps
```

Rules:

1. Safe, idiomatic Linux code — no reckless sudo, XDG base directory standards.
2. Only real, existing libraries and packages — no invented dependencies.
3. Each project ships: source, tests, systemd unit, Dockerfile, README, LICENSE.
4. Each project carries a self-review checklist (security, deps, edge cases).
5. Clear local test instructions for the human operator.
6. Every project is tested to work before it is uploaded.
7. All canonical assets are always generated — no exceptions.

## 🤝 Contributing

The Kernel Kraken is a small family project. Projects are reviewed by a human before
they land here. The lair is open, the kraken is friendly — be excellent to each other.

## 📄 License

MIT — see each project's LICENSE file.

---

*Built with AI assistance. A family collection — Linux-first, community-driven.*
