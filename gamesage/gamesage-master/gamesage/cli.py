"""The gamesage CLI: start / end / watch / last / report."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from gamesage import __version__, monitor, report, rules, session, steam

BANNER = r"""
  ╭──────────────────────────────────────╮
  │   🐧 GAMESAGE — the session sage!    │
  ╰──────────────────────────────────────╯
"""


def _peak_gpu_from_session(sess: dict) -> float | None:
    peak = None
    for s in sess.get("samples", []):
        for k, v in s.get("temps", {}).items():
            if "gpu" in k.lower() and (peak is None or v > peak):
                peak = v
    return peak


def cmd_start(args: argparse.Namespace) -> int:
    name = args.game
    appid = None
    if name and not name.isdigit():
        appid = steam.find_appid(name)
        if appid and not name.lower() == (steam.appid_name(appid) or "").lower():
            pass  # keep the user's friendly name
    if name and name.isdigit():
        appid = int(name)
        resolved = steam.appid_name(appid)
        if resolved:
            name = resolved
    if not name:
        print("  🧐 No game given — try: gamesage start \"Cairn\"")
        return 1
    sess = session.start_session(name, appid)
    print(BANNER)
    print(f"  ⏱ Session started: {sess['started']} — game: {name}"
          + (f" [{appid}]" if appid else ""))
    print("  🎮 Now launch the game and play! When you're done, run:")
    print("  💾 `gamesage end` — your report is saved automatically.")
    print("  📄 The report saves to your gaming-reports folder (open the .html!).")
    return 0


def cmd_end(args: argparse.Namespace) -> int:
    sess = session.end_session(args.session)
    if not sess:
        print("  🧐 No active session found — start one with: gamesage start \"Game\"")
        return 1
    # collect the extra data
    mangohud_log = monitor.find_mangohud_log()
    mh = monitor.parse_mangohud(mangohud_log) if mangohud_log else None
    proton = None
    shader_bytes = 0
    if sess.get("appid"):
        proton = monitor.proton_version(int(sess["appid"]))
        shader_bytes = steam.shader_cache_size(int(sess["appid"]))
    stats = report.build_stats(sess, {
        "mangohud": mh,
        "proton": proton,
        "shader_bytes": shader_bytes,
        "cpu_count": monitor.cpu_count(),
    })
    recs = rules.recommend({
        "game": sess.get("game", ""),
        "avg_fps": mh.get("avg_fps") if mh else None,
        "min_fps": mh.get("min_fps") if mh else None,
        "peak_gpu": stats.get("peak_gpu"),
        "peak_cpu": stats.get("peak_cpu_pct"),
        "shader_bytes": shader_bytes,
        "session_minutes": stats["duration_secs"] / 60.0,
        "mangohud_present": mh is not None,
    })
    print(BANNER)
    print(report.terminal_report(stats, recs))
    # save the HTML report
    out = session.report_dir() / f"{sess['game'].replace(' ', '-')}-{sess['id'][:8]}.html"
    report.html_report(stats, recs, out)
    print(f"  📄 Report saved: {out}")
    print("  💾 The report is saved after every playthrough — open the .html to view it!")
    return 0


def cmd_last(args: argparse.Namespace) -> int:
    files = sorted(session.report_dir().glob("*.html"))
    if not files:
        print("  🧐 No reports yet — finish a session with `gamesage end` first!")
        return 1
    p = files[-1]
    print(f"  📄 Latest report: {p}")
    print(f"  📂 Folder: {session.report_dir()}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """Auto-mode: detect a running Steam game, then report when it closes."""
    print("  👀 Watching for a running Steam game (Ctrl+C to stop)...")
    seen: set[int] = set()
    active: dict[int, dict] = {}
    try:
        while True:
            for root in [Path(os.path.expanduser("~/.steam/steam")),
                         Path(os.path.expanduser("~/.local/share/Steam"))]:
                appid_file = root / "steamapps" / "appid.log"
                if not appid_file.exists():
                    continue
                try:
                    current = {
                        int(line.strip()) for line in appid_file.read_text(
                            encoding="utf-8", errors="replace").splitlines()
                        if line.strip().isdigit()
                    }
                except (OSError, ValueError):
                    continue
                for appid in current:
                    if appid not in seen:
                        name = steam.appid_name(appid) or str(appid)
                        seen.add(appid)
                        sess = session.start_session(name, appid)
                        active[appid] = sess
                        print(f"  ▶ Detected: {name} [{appid}] — session started!")
                for appid in list(active):
                    if appid not in current:
                        sess = session.end_session(active[appid]["id"])
                        if sess:
                            print(f"  ⏹ Game closed: {sess['game']} — reporting!")
                        del active[appid]
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n  👋 Watch stopped.")
    return 0


def cmd_watcher(args: argparse.Namespace) -> int:
    """Internal: the detached background sampler for a session."""
    sid = args.session
    try:
        while True:
            sess = session.load_session(sid)
            if not sess or sess.get("ended"):
                break
            session.sample(sess)
            time.sleep(20)
    except (KeyboardInterrupt, Exception):
        pass
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    files = sorted(session.report_dir().glob("*.html"))
    if args.file:
        p = Path(args.file)
    elif files:
        p = files[-1]
    else:
        print("  🧐 No report to show — play a session first!")
        return 1
    if p.exists():
        print(f"  📄 Report: {p}")
        print("  Open it in a browser to view the full report.")
        return 0
    print(f"  ⚠️ Not found: {p}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gamesage",
        description="The Linux gamer's session sage — report + tweaks after every playthrough.",
    )
    parser.add_argument("--version", action="version", version=f"gamesage {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="start a session (run BEFORE the game)")
    p_start.add_argument("game", nargs="?", help="game name or Steam appid")
    p_start.set_defaults(func=cmd_start)

    p_end = sub.add_parser("end", help="end the session + save the report")
    p_end.add_argument("--session", help="specific session id (optional)")
    p_end.set_defaults(func=cmd_end)

    p_watch = sub.add_parser("watch", help="auto-detect the running game + auto-report")
    p_watch.set_defaults(func=cmd_watch)

    p_last = sub.add_parser("last", help="show the latest report")
    p_last.set_defaults(func=cmd_last)

    p_rep = sub.add_parser("report", help="show the latest (or a given) report")
    p_rep.add_argument("--file", help="path to a specific report file")
    p_rep.set_defaults(func=cmd_report)

    p_w = sub.add_parser("_watch", help=argparse.SUPPRESS)
    p_w.add_argument("session")
    p_w.set_defaults(func=cmd_watcher)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
