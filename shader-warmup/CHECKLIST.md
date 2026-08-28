# Self-review checklist — shader-warmup

## Security notes
- The tool only launches the user's own Steam with `-applaunch`; no elevated privileges.
- All file operations are read-only on the compatdata tree (except the cache files
  DXVK itself writes during the warm-up launch).
- The `--appid` argument is passed to Steam's `-applaunch`; it is validated to be a
  simple string by argparse. Steam rejects non-numeric appids harmlessly.

## Full dependency list
- Python 3.10+ (stdlib only: argparse, json, os, pathlib, shutil, subprocess, sys, time)
- `steam` binary (optional — required only for the actual warm-up launch)
- `pytest` (development/tests only)

## Known edge cases
- No Steam installed → warm-up reports "steam not found" (exit 1) — `--check` still works.
- Game not in compatdata → "compatdata for <game> not found" (exit 1).
- Game name search relies on appinfo; games whose appinfo is missing must use `--appid`.
- The warm-up launches the game windowed for ~90s; games that ignore `-windowed` may
  flash a window on the desktop.
- A game that is already running will conflict with the warm-up launch; run the tool
  before starting the game.
- Shared Steam library (second drive) compatdata is not auto-discovered; use `--appid`
  if the game lives there.

## Local test instructions (human operator)
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -e .`
3. `pytest` → expect 12/12 passing.
4. `shader-warmup "SomeGame"` → expect a "not found" message (exit 1) on a machine
   without that game — proves the lookup path runs.
5. `shader-warmup "SomeGame" --json` → expect a JSON object with `"ok": false`.
6. On a machine with Steam: `shader-warmup "<a game you own>" --check` → "Already warm"
   or the warm-up runs once.
