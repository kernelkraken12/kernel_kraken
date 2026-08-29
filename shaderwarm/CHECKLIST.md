# CHECKLIST — shaderwarm self-review (the kernel_kraken standard)

## 🔒 Security notes

- **No sudo, ever.** Reads only user-owned Steam paths + `$HOME/.local`/`$HOME/.cache`.
- **No secrets.** No credentials, no keys, no tokens.
- **No shell injection.** The game query is used as a plain string match; no
  user input is ever interpolated into a shell command.
- **Launch safety**: the `warm` command invokes `steam steam://rungameid/<appid>`
  — the standard, well-known external-launch protocol. The appid is an integer
  parsed from the real appmanifest files, never free-form input.
- **Deletion safety**: `clear` requires an explicit `--yes` and prints exactly
  what will be removed first. Nothing is ever deleted without confirmation.
- **Hardened systemd unit** (example): `PrivateTmp`, `ProtectSystem=full`,
  `ProtectHome=read-only`.

## 📦 Full dependency list

- **Runtime**: Python 3.10+ **standard library only** — `argparse`, `json`,
  `os`, `re`, `shutil`, `subprocess`, `tarfile`, `time`, `pathlib`,
  `dataclasses`, `sys`. Zero third-party packages.
- **External (optional, runtime)**: the `steam` client binary — used ONLY by
  the `warm` command to launch a game (the standard external-launch route).
- **Install**: `bash`, `python3` — nothing else.
- **Tests**: Python `unittest` (stdlib) + `unittest.mock`.

## 🧪 Known edge-cases

1. **Steam not installed**: clear error + the `$STEAM_ROOT` hint, exit 1.
2. **Custom Steam root** (flatpak/snap/Nix): covered by `$STEAM_ROOT` override
   and the extra known paths; if none match, the error tells the user how.
3. **Multi-library setups** (games on other drives): `libraryfolders.vdf` is
   parsed so caches in every library are found.
4. **A game with no cache yet**: reported as `cold` with a clear "warm it up"
   hint — never a crash.
5. **Cache freshness vs size**: size is the honest proxy for warmth; a small
   but fully-warmed game (few shaders) may show `cold-ish` — the CHECKLIST
   documents this so nobody misreads it as a bug.
6. **`warm` with no Steam client**: `subprocess.Popen(["steam", ...])` fails
   harmlessly (the error is swallowed) — the watch mode still works once the
   game runs.
7. **Concurrent game updates**: a cache that stops growing for a long time may
   look `warming` — the `status` command's age heuristic (30 days) bounds it.
8. **Unicode/emoji in game names**: handled (f-string widths approximate; the
   scan table truncates names to 30 chars).

## ✅ Local test instructions (run before any release)

```bash
# from the project root (shaderwarm/)
python3 -m unittest discover -s tests -v        # the fake-Steam-tree tests
bash install.sh                                  # install to ~/.local
export PATH="$HOME/.local/bin:$PATH"             # if needed
shaderwarm scan                                  # live check (Steam present)
shaderwarm status "cairn"                        # case-insensitive match
shaderwarm warm "cairn"                          # launches the game via steam://
shaderwarm warm "cairn" --watch                  # watch the cache grow
shaderwarm backup "cairn"                        # tar to the XDG data dir
shaderwarm clear "cairn"                         # must refuse without --yes
shaderwarm clear "cairn" --yes                   # then clears
shaderwarm scan --json | python3 -m json.tool    # JSON output valid
```

Tested on a fake Steam tree (tests) + a live install on the family homelab
(cn host) — the warmup launch itself needs a real Steam client + GPU, so the
PC-side test is the human's step (per the standard: human validates before
release).

## ✅ Repo metadata (rule #8)

- **Description**: "Warm shaders, smooth FPS — scan, warm up, back up and
  clear Steam's shader caches on Linux (DXVK/vkd3d)."
- **Topics**: `linux-cli`, `shader-cache`, `dxvk`, `vkd3d`, `proton`,
  `linux-gaming`, `steam`, `cli`, `gaming`, `foss`
