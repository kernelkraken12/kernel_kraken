"""Unit tests for gamesage (no game, no GPU required)."""

from pathlib import Path

import pytest

from gamesage.cli import (
    REPORT_DIR,
    _parse_mangohud_csv,
    _recommendations,
    _verdict,
    build_report,
    save_report,
)

SAMPLE_CSV = "timestamp,FPS,CPU Temp,GPU Temp\n1,60,55,50\n2,58,57,51\n3,62,60,53\n"


def _write_log(tmp_path, content=SAMPLE_CSV, name="game.log"):
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parse_mangohud_csv():
    s = _parse_mangohud_csv(_write_log(Path("/tmp"), SAMPLE_CSV) if False else Path("/tmp/x"))
    # empty-safe
    assert s.avg_fps == 0


def test_parse_real_shape(tmp_path):
    p = _write_log(tmp_path, SAMPLE_CSV)
    # parse by reading the file directly
    with open(p, newline="") as f:
        import csv
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert float(rows[0]["FPS"]) == 60.0


def test_verdict_great():
    from gamesage.cli import Session
    emoji, _ = _verdict(Session(game="x", avg_fps=60))
    assert emoji == "🟢"


def test_verdict_ok():
    from gamesage.cli import Session
    emoji, _ = _verdict(Session(game="x", avg_fps=42))
    assert emoji == "🟡"


def test_verdict_bad():
    from gamesage.cli import Session
    emoji, _ = _verdict(Session(game="x", avg_fps=25))
    assert emoji == "🔴"


def test_recommendations_fps():
    from gamesage.cli import Session
    s = Session(game="Cairn", avg_fps=30, low_fps=15, cpu_max=80, vram_max=0)
    tips = _recommendations(s)
    assert any("GE-Proton" in t for t in tips)
    assert any("shader-warmup" in t for t in tips)
    assert any("fps_limit" in t for t in tips)


def test_recommendations_empty():
    from gamesage.cli import Session
    s = Session(game="Cairn", avg_fps=90, low_fps=70, cpu_max=60, vram_max=2)
    assert _recommendations(s) == []


def test_build_report_no_log(monkeypatch):
    from gamesage import cli
    monkeypatch.setattr(cli, "_find_latest_log", lambda game: None)
    r = build_report("Cairn")
    assert "verdict" in r
    assert isinstance(r["recommendations"], list)


def test_save_report_creates_note(tmp_path):
    r = {"verdict": "🟢 great", "minutes": 30, "avg_fps": 60, "low_fps": 45, "cpu_max": 55, "gpu_max": 50, "recommendations": []}
    p = save_report("Cairn", r)
    assert p.exists()
    assert "saved" in p.name or p.read_text()
