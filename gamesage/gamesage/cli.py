#!/usr/bin/env python3
"""gamesage — after a playthrough, turn your game session into a simple report + smart recommendations.

Usage:
    gamesage "Cairn"             # report from the latest session (saved + printed)
    gamesage "Cairn" --detailed  # full stats for the nerds
    gamesage "Cairn" --json      # machine-readable
"""

import argparse
import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

__version__ = "0.1.0"

REPORT_DIR = Path.home() / ".local" / "share" / "gamesage"


@dataclass
class Session:
    game: str
    minutes: float = 0.0
    avg_fps: float = 0.0
    low_fps: float = 0.0
    cpu_max: float = 0.0
    gpu_max: float = 0.0
    vram_max: float = 0.0
    proton: str = "unknown"


def _parse_mangohud_csv(path: Path) -> Session:
    s = Session(game=path.parent.name)
    fps = []
    cpu = []
    gpu = []
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return s
    for r in rows:
        try:
            fps.append(float(r.get("FPS", 0)))
            cpu.append(float(r.get("CPU Temp", 0) or 0))
            gpu.append(float(r.get("GPU Temp", 0) or 0))
        except (TypeError, ValueError):
            continue
    if fps:
        s.avg_fps = round(sum(fps) / len(fps), 1)
        s.low_fps = round(sorted(fps)[max(0, int(len(fps) * 0.01) - 1)], 1)
        s.minutes = round(len(fps) / 60, 1)  # ~1 sample/sec
    if cpu:
        s.cpu_max = max(cpu)
    if gpu:
        s.gpu_max = max(gpu)
    return s


def _find_latest_log(game: str) -> Path | None:
    """Look for the newest mangohud log matching the game (or any, if unnamed)."""
    candidates = sorted(REPORT_DIR.glob("*/**/*.csv")) + sorted(Path.home().glob("MANGOHUD*.csv"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _recommendations(s: Session) -> list[str]:
    tips = []
    if s.avg_fps and s.avg_fps < 45:
        tips.append("Low FPS — try GE-Proton + gamemode: add `gamemoderun %command%` to the launch options.")
    if s.low_fps and s.low_fps < 30:
        tips.append(f"Stutters (low 1% FPS) — pre-bake shaders with `shader-warmup \"{s.game}\"`.")
    if s.cpu_max and s.cpu_max > 75:
        tips.append("Hot CPU — cap frames: add `MANGOHUD_CONFIG=fps_limit=60 %command%` to the launch options.")
    if s.vram_max and s.vram_max > 6:
        tips.append("High VRAM — try lowering texture quality one notch.")
    return tips


def _verdict(s: Session) -> tuple[str, str]:
    if s.avg_fps >= 55:
        return "🟢", "Your game ran GREAT — smooth and happy!"
    if s.avg_fps >= 35:
        return "🟡", "Your game ran OK — a couple of quick wins could make it shine."
    return "🔴", "Your game needs some help — the tips below should make a real difference."


def build_report(game: str, detailed: bool = False) -> dict:
    log = _find_latest_log(game)
    s = Session(game=game)
    if log:
        s = _parse_mangohud_csv(log)
    else:
        s.minutes = 0
    recs = _recommendations(s)
    emoji, verdict = _verdict(s)
    report = {
        "game": s.game,
        "minutes": s.minutes,
        "avg_fps": s.avg_fps,
        "low_fps": s.low_fps,
        "cpu_max": s.cpu_max,
        "gpu_max": s.gpu_max,
        "verdict": f"{emoji} {verdict}",
        "recommendations": recs,
    }
    return report


def save_report(game: str, report: dict) -> Path:
    out = REPORT_DIR / game
    out.mkdir(parents=True, exist_ok=True)
    path = out / "latest.txt"
    path.write_text(
        f"{report['verdict']}\n"
        f"Session: {report['minutes']} min | avg {report['avg_fps']} FPS | 1% low {report['low_fps']}\n"
        f"Temps: CPU {report['cpu_max']}°C max | GPU {report['gpu_max']}°C max\n"
        + ("\n".join(f"- {r}" for r in report["recommendations"]) or "- no tips needed, nice!")
    )
    return path


def main() -> int:
    ap = argparse.ArgumentParser(prog="gamesage", description="Simple game session reports + smart tips.")
    ap.add_argument("game", nargs="?", default="", help="Game name (optional if a log exists)")
    ap.add_argument("--detailed", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    report = build_report(args.game or "latest-session", args.detailed)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print()
    print(f"   __  __  ___  ____  ___  ___  ___  ____  _____")
    print(f"  / / / / / _ \\|  _ \\/ _ \\/ _ \\/ _ \\|  _ \\| ____|  (the sage speaks!)")
    print()
    print(report["verdict"])
    if args.detailed:
        print(f"Session: {report['minutes']} min | avg {report['avg_fps']} FPS | 1% low {report['low_fps']} | CPU {report['cpu_max']}°C | GPU {report['gpu_max']}°C")
    if report["recommendations"]:
        print("💡 QUICK WINS:")
        for r in report["recommendations"]:
            print(f"  • {r}")
    saved = save_report(args.game or "latest-session", report)
    print()
    print(f"📄 Your report has been saved to: {saved}")
    print("   (Come back any time — your past reports live here too.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
