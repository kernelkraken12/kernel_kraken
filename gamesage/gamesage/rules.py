"""The recommendations engine: session data -> plain-English tweaks."""

from __future__ import annotations

# Known per-game advice (the honest, community-common knowledge — guidelines only!)
GAME_TIPS: dict[str, list[str]] = {
    "cairn": [
        "Cairn is CPU-bound on Linux — try Proton-GE and add the launch option: `gamemoderun %command%`",
        "FSR + a ~85% render scale gives a solid FPS lift on mid-range GPUs.",
    ],
    "the last caretaker": [
        "The Last Caretaker's engine is heavy on single-core CPU — close background apps before playing.",
        "If stutter appears, a warm shader cache (play a few minutes first) helps a lot.",
    ],
    "elden ring": [
        "Elden Ring benefits from `PROTON_USE_WINED3D=1` on some GPUs — only if Vulkan glitches.",
        "A 60 FPS cap avoids thermal spikes on long sessions.",
    ],
    "cyberpunk": [
        "Cyberpunk loves FSR — try the Ultra-Performance preset on mid-range GPUs.",
    ],
}


def _game_tips(game: str) -> list[str]:
    key = game.lower().strip()
    for known, tips in GAME_TIPS.items():
        if known in key:
            return list(tips)
    return []


def recommend(data: dict) -> list[dict]:
    """Return a ranked list of {level, text} recommendations.

    data keys: avg_fps, min_fps, peak_gpu, peak_cpu, gpu_name,
               shader_bytes, session_minutes, mangohud_present
    """
    out: list[dict] = []

    def add(level: str, text: str) -> None:
        out.append({"level": level, "text": text})

    avg_fps = data.get("avg_fps")
    min_fps = data.get("min_fps")
    peak_gpu = data.get("peak_gpu")
    peak_cpu = data.get("peak_cpu")

    # FPS-based rules
    if avg_fps is not None and avg_fps < 30:
        add("high", "FPS is low (under 30). Try a newer Proton version (Proton-GE), "
                   "lower the graphics preset, or enable FSR/upscaling.")
    elif avg_fps is not None and avg_fps < 55:
        add("mid", "FPS is modest. FSR/upscaling or a small render-scale drop usually "
                   "gains a clean 20–40%.")
    if min_fps is not None and min_fps < 20 and avg_fps is not None and avg_fps > 40:
        add("mid", "The frame-time spikes (min FPS much lower than average) often mean "
                   "shader-compile stutter on the first run — it smooths out after a session.")

    # GPU temp rules
    if peak_gpu is not None and peak_gpu >= 85:
        add("high", f"The GPU peaked at {peak_gpu:.0f}°C — quite hot. A 60 FPS cap or "
                    "upscaling will cool it down and keep the clocks stable.")
    elif peak_gpu is not None and peak_gpu >= 75:
        add("low", f"The GPU peaked at {peak_gpu:.0f}°C — warm but fine. A frame cap "
                   "is the easy win if the fans are loud.")

    # CPU rules
    if peak_cpu is not None and peak_cpu > 80 and avg_fps is not None and avg_fps < 60:
        add("mid", "The CPU was the bottleneck (high load with modest FPS). Close "
                   "background apps or try `gamemoderun %command%` as a launch option.")
    if peak_cpu is not None and peak_cpu > 90:
        add("low", "CPU usage was very high — check for background tasks during play.")

    # MangoHud note
    if not data.get("mangohud_present", True):
        add("low", "Install MangoHud for live FPS overlays and more precise numbers next time "
                   "(the report used system sensors only).")

    # Shader cache note
    shader_bytes = data.get("shader_bytes") or 0
    if shader_bytes < 1_000_000 and data.get("session_minutes", 0) > 5:
        add("low", "The shader cache was empty/tiny — first-time shader compiles cause early "
                   "stutter. A warm cache makes the next session noticeably smoother.")

    # Per-game known tips
    for tip in _game_tips(data.get("game", "")):
        add("low", tip)

    return out
