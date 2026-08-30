"""Session state: XDG storage, start/end, and the background watcher."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

APP = "gamesage"


def state_dir() -> Path:
    xdg = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    d = Path(xdg) / APP
    d.mkdir(parents=True, exist_ok=True)
    return d


def report_dir() -> Path:
    xdg = os.environ.get("XDG_DOCUMENTS_DIR")
    if xdg:
        d = Path(xdg) / "gaming-reports"
    else:
        d = Path.home() / "Documents" / "gaming-reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def session_file(session_id: str | None = None) -> Path:
    if session_id:
        return state_dir() / f"session-{session_id}.json"
    return state_dir() / "current.json"


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def start_session(game: str, appid: int | None) -> dict:
    """Create a new session record + spawn the background watcher."""
    sid = time.strftime("%Y%m%d-%H%M%S")
    session = {
        "id": sid,
        "game": game,
        "appid": appid,
        "started": _now(),
        "ended": None,
        "samples": [],
        "watcher_pid": None,
    }
    session_file(sid).write_text(json.dumps(session, indent=2), encoding="utf-8")
    session_file().write_text(json.dumps({"current": sid}), encoding="utf-8")
    # spawn the detached watcher: gamesage _watch <sid>
    watcher = subprocess.Popen(
        [sys.executable, "-m", "gamesage", "_watch", sid],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    session["watcher_pid"] = watcher.pid
    _write(session_file(sid), session)
    return session


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_session(sid: str | None = None) -> dict | None:
    if sid:
        p = session_file(sid)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return None
    cur = session_file()
    if cur.exists():
        try:
            meta = json.loads(cur.read_text(encoding="utf-8"))
            sid = meta.get("current")
            if sid:
                return load_session(sid)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def end_session(sid: str | None = None) -> dict | None:
    session = load_session(sid)
    if not session:
        return None
    # stop the watcher
    pid = session.get("watcher_pid")
    if pid:
        try:
            os.kill(int(pid), 15)
        except (OSError, ValueError):
            pass
    session["ended"] = _now()
    _write(session_file(session["id"]), session)
    return session


def sample(session: dict) -> None:
    """Append a lightweight system sample to the session."""
    from gamesage import monitor

    sample_data = monitor.sample_once()
    session.setdefault("samples", []).append(sample_data)
    _write(session_file(session["id"]), session)
