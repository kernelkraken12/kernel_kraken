# 🐙 The Kernel Kraken's Lair

**Open-source software, Linux-first tools, and homelab experiments.**

A mixed collection of practical projects built for the self-hosted and Linux-first community: CLI tools, TUI apps, Proxmox / homelab utilities, system scripts, and the occasional experimental idea that escapes the depths.

> *Built in the desert. Released by the kraken.*

---

## 🎯 What Lives Here

| Lane | What you'll find |
|---|---|
| 🖥️ CLI tools | Practical command-line utilities for Linux |
| 🎨 TUI apps | Terminal user interfaces that make the shell prettier |
| 🏠 Homelab | Proxmox helpers, mirror utilities, monitoring fragments |
| 📜 System scripts | Safe, idiomatic setup / hardening / maintenance scripts |
| 🧪 Experiments | Proof-of-concept code, half-finished ideas, throwaway tests |

Mostly Linux. Always FOSS. MIT-licensed. Human-reviewed.

---

## 🛠️ Ground Rules (the family standard)

Every project in this lair ships complete and reviewable:

- **Safe, idiomatic code** — no reckless `sudo`, no hard-coded absolute paths, XDG base directory standards respected
- **Real dependencies only** — every library, binary, and flag actually exists
- **Full project package** — `src/` + `tests/` + example `systemd/` unit + `Dockerfile` + `README.md` + `LICENSE` (MIT)
- **Self-review checklist** — security notes, dependency list, known edge cases (`CHECKLIST.md`)
- **Local test instructions** — exact steps to run and validate before any release
- **Human approval gate** — nothing is committed or pushed without explicit human review and an "Approved"

---

## 🗂️ Canonical Project Tree

```
<project>/
├── src/
├── tests/
├── systemd/<name>.service   # example unit
├── examples/                # sample configs
├── android/                 # included only when Android code exists
├── Dockerfile
├── .gitignore
├── README.md                # primary-repo note + AI-assistance disclosure
├── LICENSE                  # MIT
└── CHECKLIST.md             # self-review: security, deps, edge cases, test steps
```

---

## 📦 The Fleet

| Project | Lane | Status |
|---|---|---|
| [**protondbcli**](./protondbcli/) — will it run on Linux, and how? | 🖥️ CLI tools | ✅ **live** (v0.1.0) |
| *(next project TBD)* | TBD | 🚧 planned |

---

## 🤝 Contributing

This is a family-run lair with a human approval gate. PRs and issues are welcome, but all changes are reviewed by hand before merging — no bots, no auto-merge, no surprises.

## 📜 License

Everything here is MIT-licensed unless a project says otherwise. Use it, learn from it, improve it — just keep the attribution.

---

**The Kernel Kraken's Lair — built in the desert, released by the kraken. 🐙**
