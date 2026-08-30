"""System monitoring: hwmon temps, CPU load, MangoHud log, Proton version."""

from __future__ import annotations

import glob
import os
import re
from pathlib import Path


def _read_int(path: str) -> int | None:
    try:
        return int(Path(path).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def hwmon_temps() -> dict[str, float]:
    """Map of sensor-name -> temperature (C)."""
    temps: dict[str, float] = {}
    for hw in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        try:
            name = (Path(hw) / "name").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        for temp in sorted(glob.glob(f"{hw}/temp*_input")):
            v = _read_int(temp)
            if v is None:
                continue
            label = temp.rsplit("/", 1)[-1].replace("_input", "")
            key = f"{name}:{label}"
            temps[key] = round(v / 1000.0, 1)
    return temps


def cpu_load() -> float | None:
    """Current 1-minute CPU load average."""
    try:
        with open("/proc/loadavg", encoding="utf-8") as f:
            return float(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def cpu_count() -> int:
    return os.cpu_count() or 1


def sample_once() -> dict:
    """A single lightweight system sample."""
    return {
        "time": __import__("time").strftime("%H:%M:%S"),
        "temps": hwmon_temps(),
        "load": cpu_load(),
    }


def find_mangohud_log() -> Path | None:
    """Locate the MangoHud log if present (XDG data dir)."""
    xdg = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    candidates = [
        Path(xdg) / "MangoHud" / "MangoHud.log",
        Path.home() / ".local/share/MangoHud/MangoHud.log",
        Path.home() / ".MangoHud.log",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_mangohud(log: Path, window_minutes: int = 30) -> dict | None:
    """Parse the LAST session block from a MangoHud log.

    MangoHud log blocks look like:
      <date> <time>  ... lines ...  (one line per frame-sample)
    We take the trailing block and average fps values.
    """
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    fps_values: list[float] = []
    for line in lines[-2000:]:
        m = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*fps\b", line, re.I)
        if m:
            try:
                fps_values.append(float(m.group(1)))
            except ValueError:
                continue
    if not fps_values:
        return None
    return {
        "samples": len(fps_values),
        "avg_fps": round(sum(fps_values) / len(fps_values), 1),
        "min_fps": round(min(fps_values), 1),
        "max_fps": round(max(fps_values), 1),
    }


def proton_version(appid: int) -> str | None:
    """Best-effort Proton version from the Steam compatdata dir."""
    for root in [
        Path(os.path.expanduser("~/.steam/steam")),
        Path(os.path.expanduser("~/.local/share/Steam")),
    ]:
        d = root / "steamapps" / "compatdata" / str(appid)
        if d.is_dir():
            version_file = d / "version"
            if version_file.exists():
                try:
                    v = version_file.read_text(encoding="utf-8").strip()
                    if v:
                        return v[:40]
                except OSError:
                    pass
            return "Proton (compatdata present)"
    return None
