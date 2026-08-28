# 🔥 shader-warmup

**Pre-bake DXVK shader caches so your Linux games start smooth — no more first-minute stutter.**

> **Primary repository:** [kernel_kraken](https://github.com/kernelkraken12/kernel_kraken)

When a Proton game runs, DXVK translates Windows shaders to Vulkan at runtime. The
first time each shader is needed, the game stutters while it compiles. `shader-warmup`
launches the game briefly in the background so those shaders get baked ahead of time —
then your real session starts smooth.

## ✨ Features

- Find a game's compatdata by name (case-insensitive)
- Warm it up automatically with a brief headless launch
- `--check` to see if a game is already warm
- `--json` output for scripts
- Works with any game that uses DXVK (Steam, Heroic, Lutris)

## 🚀 Quick start

```bash
# Install (pick one)
uv tool install shader-warmup
pipx install shader-warmup
pip install .          # from this repo

# Check a game
shader-warmup "Cairn"

# Check without warming
shader-warmup "Cairn" --check

# JSON for scripts
shader-warmup "Cairn" --json
```

## 🤖 Automatic warm-up (recommended)

Paste this into the game's **Steam launch options**:

```
shader-warmup "Cairn" && %command%
```

Every launch: it checks the cache, warms if needed (about 90 s the first time), then
starts the game automatically. First launch is a bit slower, every launch after is
instant.

## 👶 New to Linux gaming?

- **DXVK** = the tool that translates DirectX shaders to Vulkan so Windows games run
  on Linux. Steam does this automatically through Proton.
- **Shader stutter** = the lag you see in the first minutes of a game while shaders
  compile. This tool removes that.
- **compatdata** = the folder where Proton keeps each game's Windows environment,
  including the shader cache.

## 🛠️ Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pytest
```

## ⚠️ Notes

- Warming needs Steam to be installed and the game to be present in compatdata.
- The first warm-up launches the game windowed for ~90 seconds in the background.
- Games that update often will need a re-warm (new shaders arrive with updates).

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Built with AI assistance. This project is part of the [kernel_kraken](https://github.com/kernelkraken12/kernel_kraken) collection — Linux-first open-source tools.*
