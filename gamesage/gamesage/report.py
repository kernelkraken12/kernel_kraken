"""Report generation: the terminal table + the friendly HTML report."""

from __future__ import annotations

import html
import time
from pathlib import Path

from gamesage import __version__


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f}KB"
    return f"{n / 1024 ** 2:.1f}MB"


def _duration(secs: float) -> str:
    secs = int(secs)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def build_stats(session: dict, extra: dict | None = None) -> dict:
    """Assemble the report data from the session + extra sources."""
    extra = extra or {}
    samples = session.get("samples", [])
    peak_gpu = None
    peak_cpu_load = None
    gpu_key = None
    for s in samples:
        temps = s.get("temps", {})
        for k, v in temps.items():
            if "gpu" in k.lower():
                if peak_gpu is None or v > peak_gpu:
                    peak_gpu = v
                    gpu_key = k
        load = s.get("load")
        if load is not None:
            peak_cpu_load = max(peak_cpu_load or 0, load)

    started = session.get("started", "")
    ended = session.get("ended") or time.strftime("%Y-%m-%d %H:%M:%S")
    duration_secs = 0
    try:
        t0 = time.mktime(time.strptime(started, "%Y-%m-%d %H:%M:%S"))
        t1 = time.mktime(time.strptime(ended, "%Y-%m-%d %H:%M:%S"))
        duration_secs = max(0, t1 - t0)
    except (ValueError, OSError):
        duration_secs = 0

    cpu_count = extra.get("cpu_count") or 1
    peak_cpu_pct = None
    if peak_cpu_load is not None:
        peak_cpu_pct = min(100.0, round(peak_cpu_load / cpu_count * 100.0, 1))

    return {
        "game": session.get("game", "unknown"),
        "appid": session.get("appid"),
        "started": started,
        "ended": ended,
        "duration_secs": duration_secs,
        "duration": _duration(duration_secs),
        "peak_gpu": peak_gpu,
        "gpu_sensor": gpu_key,
        "peak_cpu_pct": peak_cpu_pct,
        "mangohud": extra.get("mangohud"),
        "proton": extra.get("proton"),
        "shader_bytes": extra.get("shader_bytes"),
        "shader_size": _fmt_size(extra.get("shader_bytes") or 0),
        "sample_count": len(samples),
    }


def terminal_report(stats: dict, recs: list[dict]) -> str:
    lines = []
    lines.append("")
    lines.append("  ┌────────────────────────────────────────────┐")
    lines.append(f"  │  🐙 GAMESAGE — SESSION REPORT              │")
    lines.append("  └────────────────────────────────────────────┘")
    lines.append(f"  🎮 Game:        {stats['game']}" + (f"  [{stats['appid']}]" if stats.get("appid") else ""))
    lines.append(f"  ⏱ Duration:    {stats['duration']}")
    if stats.get("proton"):
        lines.append(f"  🎭 Proton:      {stats['proton']}")
    if stats.get("peak_gpu") is not None:
        lines.append(f"  🌡 Peak GPU:    {stats['peak_gpu']:.0f}°C")
    if stats.get("peak_cpu_pct") is not None:
        lines.append(f"  🧠 Peak CPU:    {stats['peak_cpu_pct']:.0f}%")
    if stats.get("mangohud"):
        m = stats["mangohud"]
        lines.append(f"  ⚡ FPS (MangoHud): avg {m['avg_fps']} · min {m['min_fps']} · max {m['max_fps']}")
    lines.append(f"  📦 Shader-cache: {stats['shader_size']}")
    lines.append("  ─────────────────────────────────────────────")
    if recs:
        lines.append("  🧠 RECOMMENDATIONS:")
        icons = {"high": "🔴", "mid": "🟡", "low": "🟢"}
        for r in recs:
            lines.append(f"    {icons.get(r['level'], '•')} {r['text']}")
    else:
        lines.append("  🟢 No tweaks needed — smooth session!")
    lines.append("")
    return "\n".join(lines)


def html_report(stats: dict, recs: list[dict], out_path: Path) -> Path:
    icons = {"high": "🔴", "mid": "🟡", "low": "🟢"}
    rows = ""
    for label, val in [
        ("Game", f"{html.escape(stats['game'])}" + (f" <code>[{stats['appid']}]</code>" if stats.get("appid") else "")),
        ("Duration", stats["duration"]),
        ("Proton", html.escape(stats["proton"] or "—")),
        ("Peak GPU temp", f"{stats['peak_gpu']:.0f}°C" if stats.get("peak_gpu") is not None else "—"),
        ("Peak CPU", f"{stats['peak_cpu_pct']:.0f}%" if stats.get("peak_cpu_pct") is not None else "—"),
        ("FPS (MangoHud)", (f"avg {stats['mangohud']['avg_fps']} · min {stats['mangohud']['min_fps']} · max {stats['mangohud']['max_fps']}" if stats.get("mangohud") else "—")),
        ("Shader cache", stats["shader_size"]),
        ("Started", html.escape(stats["started"])),
    ]:
        rows += f"<tr><td class='lbl'>{label}</td><td>{val}</td></tr>\n"

    rec_html = ""
    if recs:
        for r in recs:
            rec_html += f"<li><span class='rec {r['level']}'>{icons.get(r['level'], '•')} {html.escape(r['text'])}</span></li>\n"
    else:
        rec_html = "<li class='rec low'>🟢 No tweaks needed — smooth session!</li>\n"

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🐙 Gamesage — {html.escape(stats['game'])}</title>
<style>
body {{ background:#0d1117; color:#e6edf3; font-family:'Segoe UI',system-ui,sans-serif;
       max-width:640px; margin:0 auto; padding:24px 16px; }}
h1 {{ color:#ff7b9c; font-size:22px; }} h2 {{ color:#7ee787; font-size:15px; margin-top:28px; }}
table {{ width:100%; border-collapse:collapse; background:#161b22; border-radius:10px; overflow:hidden; }}
td {{ padding:9px 14px; border-bottom:1px solid #21262d; font-size:14px; }}
td.lbl {{ color:#8b949e; width:38%; }}
ul {{ list-style:none; padding:0; }} li {{ padding:9px 12px; margin:6px 0; border-radius:8px;
     background:#161b22; font-size:14px; }}
.rec.high {{ border-left:4px solid #f85149; }} .rec.mid {{ border-left:4px solid #d29922; }}
.rec.low {{ border-left:4px solid #3fb950; }}
.footer {{ margin-top:30px; color:#484f58; font-size:11px; }}
code {{ background:#21262d; padding:1px 5px; border-radius:4px; }}
</style></head><body>
<h1>🐙 Gamesage — Session Report</h1>
<p style="color:#8b949e">{html.escape(stats['started'])} → {html.escape(stats['ended'])}</p>
<table>{rows}</table>
<h2>🧠 Recommendations</h2>
<ul>{rec_html}</ul>
<p class="footer">Made with <a href="https://github.com/kernelkraken12/kernel_kraken">gamesage</a> v{__version__}
 — session data from your system sensors; recommendations are friendly guidelines, not guarantees.</p>
</body></html>"""
    out_path.write_text(page, encoding="utf-8")
    return out_path
