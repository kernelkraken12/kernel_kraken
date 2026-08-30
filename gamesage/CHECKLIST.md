# Self-review checklist — gamesage

## Security notes
- Reads only the user's own MangoHud logs and writes only under `~/.local/share/gamesage/`.
- No root, no network, no shell execution. Pure stdlib.

## Dependencies
- Python 3.10+ stdlib only (argparse, csv, json, dataclasses, pathlib). Zero pip deps at runtime.

## Known edge cases
- No MangoHud log found → report shows a neutral verdict and tells the player how to enable logging.
- Log with missing/empty columns → gracefully falls back to zeros (no crash).
- Very short sessions (<10 samples) → the 1% low may equal the min FPS; report still valid.
- Non-ASCII game names → handled (utf-8 safe file writes).

## Exact test steps (run before any release)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install pytest
pytest tests/ -q          # expect ALL pass
gamesage "Cairn"          # smoke: prints a report + saves the note
gamesage "Cairn" --json   # smoke: valid JSON out
```
