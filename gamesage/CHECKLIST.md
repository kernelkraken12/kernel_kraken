# gamesage — self-review checklist (the kraken standard)

## Security notes
- No sudo anywhere. Installs to `~/.local` (XDG), reads system sensors read-only.
- No telemetry, no network calls, no uploads. All data stays local.
- `install.sh` only copies files into `$HOME/.local` — no system writes.
- The background sampler is a child process of the session; it is killed on
  `gamesage end`.

## Dependency list (real, minimal)
- Python 3.10+ (stdlib only — `json`, `glob`, `re`, `subprocess`, `argparse`,
  `pathlib`, `time`, `html`).
- MangoHud (optional, read-only log parsing if present).
- Steam (optional — reads local manifests only if a Steam install exists).

## Known edge-cases
- No Steam install → appid/game-name resolution returns None; the report still
  works with the name you typed.
- No MangoHud → FPS rows show "—" and the report suggests installing MangoHud
  (never invents FPS numbers).
- No hwmon sensors (e.g. containers/VM) → temp rows show "—".
- Game not found by name → appid stays None; shader-cache/Proton rows show "—".
- `gamesage end` with no session → clear "no session" message, exit 1.
- Very short sessions (<20s, zero samples) → report still prints, duration ~0.
- The watcher auto-stops when the session ends (checked every sample tick).

## Test steps (run these before release)
```bash
python3 -m unittest discover -s tests -v          # expect 10/10 pass
gamesage start "Cairn"                             # session begins + watcher spawns
sleep 5 && gamesage end                            # report prints + HTML saves
gamesage last                                      # points at the saved report
python3 -m gamesage --version                      # prints gamesage 0.1.0
bash -n install.sh                                 # installer syntax check
```
