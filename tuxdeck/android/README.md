# 🐧⚡ TuxDeck

**Mission control for your Linux fleet, in your pocket.** An Android cockpit for your Fedora (or any SSH-able) machine: live stats, systemd control, journal, a real PTY terminal, and a big DeLorean-style power button with Wake-on-LAN.

*"roads? where we're going, we don't need roads."*

## Features (v0.1.0 — Phase 1 of the TuxDeck roadmap)

- **Time-circuits live stats** — CPU / MEM / LOAD as an always-visible LED strip, updating every 3 s over a single SSH round-trip (two `/proc/stat` samples, meminfo, loadavg, uptime, df — parsed on-device).
- **Overview** — gauge rings, braille-character CPU history sparkline, system card, per-mount disk bars.
- **Hero power button** — glowing ring: tap to **Wake-on-LAN** when the machine is off; power icon (top-right) opens Suspend / Reboot / Poweroff / Lock session, each behind a confirmation.
- **Services** — systemd unit list with state colors and failed-unit counter.
- **Journal** — `journalctl -n 120` on demand, selectable text.
- **Real terminal** — interactive PTY shell (xterm-256color), streaming output with ANSI/OSC cleanup, input with Enter-to-run.
- **Auth** — password or imported OpenSSH key file (Ed25519/ECDSA/RSA; full BouncyCastle is bundled because Android's built-in "BC" lacks X25519).
- **Multi-host** — add as many machines as you like; MAC is fetched automatically on first connect for WoL.

## The DeLorean touch

Stainless-steel panels, time-circuits LED readouts, a pulsing flux capacitor on the stats strip, ASCII Tux on the home screen, and `1.21 GIGAWATTS` when you wake a machine. The `OUTATIME` plate is on the footer, where it belongs.

## Requirements

- The host: any machine running `sshd` (Fedora ships it; enable with `sudo systemctl enable --now sshd`).
- The phone: Android 9+. App permission: INTERNET only (it talks solely to hosts you configure — no cloud, no telemetry).

## Usage

1. Install `TuxDeck-v0.1.0-release.apk`.
2. **+** → label, hostname/IP, port (22), user → password or *import SSH key file*.
3. The cockpit opens: LED strip goes live, and the host's MAC is captured for WoL.
4. Power icon (top right) → Suspend / Reboot / Poweroff / Lock (each asks first). Next morning: tap the big button to wake it.

> Note: password auth is stored in the app's private storage for now (Android Keystore hardening is on the roadmap). If someone gets root on your phone, they get your SSH creds — use a key with a restricted user if that worries you.

## Roadmap (agreed with the user)

- **Phase 2 — files:** WebDAV server (phone appears in Dolphin via `webdav://`), USB `adb forward` fast lane, Cast-to-PC (`xdg-open` over SSH), Photo Handoff → PC clipboard (tiny `wl-copy` helper).
- **Phase 3:** Relay share-target (`yt-dlp`/`aria2c` on the PC from any app's Share menu), dnf Cart + Updates tab, Couch Control (mpv/VLC).
- **Phase 4:** Peek — VNC remote desktop (krfb; full input on X11, helper for Wayland), Quick Settings tiles, mDNS discovery, custom SSH command buttons, Keystore-secured secrets.

## Build

```
./gradlew assembleRelease
```

Stack: Kotlin, Jetpack Compose (Material 3), sshj + BouncyCastle, coroutines. Signed release APK: `TuxDeck-v0.1.0-release.apk`.

## Verified live (2026-10-01)

Tested from the emulator against a real Fedora host over SSH (key auth, Ed25519):
- Live LED strip: CPU/MEM/LOAD matching `uptime`/`free` on the host ✓
- Overview: hostname, uptime, load, memory, per-mount disk bars ✓
- Terminal: real PTY — `uname -a`, `date`, command echo verified on the host ✓
- Journal: live `journalctl` output ✓
- WoL path exercised (machine already awake; full wake test needs a suspended host)
