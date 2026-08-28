"""Unit tests for shader-warmup (no Steam, no network required)."""

from pathlib import Path

import pytest

from shader_warmup.cli import (
    DXVK_CACHE_SUFFIXES,
    cache_size,
    is_warm,
    render,
    shader_files,
)


def make_compatdir(tmp_path: Path, files: dict[str, int]) -> Path:
    """Create a fake compatdata dir with sized cache files."""
    for name, size in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\x00" * size)
    return tmp_path


def test_shader_files_finds_dxvk_caches(tmp_path):
    d = make_compatdir(tmp_path, {"a.dxvk-cache": 100, "b.dxvk-cache.v2": 200})
    found = shader_files(d)
    assert len(found) == 2
    assert all(any(s in f.name for s in DXVK_CACHE_SUFFIXES) for f in found)


def test_shader_files_ignores_other_files(tmp_path):
    d = make_compatdir(tmp_path, {"notes.txt": 50, "config.xml": 10})
    assert shader_files(d) == []


def test_cache_size_sums_bytes(tmp_path):
    d = make_compatdir(tmp_path, {"a.dxvk-cache": 512, "b.dxvk-cache.v2": 768})
    assert cache_size(d) == 1280


def test_is_warm_below_threshold(tmp_path):
    d = make_compatdir(tmp_path, {"a.dxvk-cache": 1024})
    assert is_warm(d, min_bytes=2048) is False


def test_is_warm_above_threshold(tmp_path):
    d = make_compatdir(tmp_path, {"a.dxvk-cache": 5 * 1024 * 1024})
    assert is_warm(d, min_bytes=1024 * 1024) is True


def test_render_warm_state():
    out = render({}, "Cairn", warm=True)
    assert "Already warm" in out
    assert "Cairn" in out


def test_render_success():
    out = render(
        {"ok": True, "baked_bytes": 2 * 1024 * 1024, "elapsed_seconds": 90},
        "Cairn",
        warm=False,
    )
    assert "Warmed up" in out
    assert "2.0 MB" in out


def test_render_failure():
    out = render({"ok": False, "reason": "steam not found"}, "Cairn", warm=False)
    assert "steam not found" in out


def test_main_requires_argument(capsys):
    from shader_warmup.cli import main

    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code == 2


def test_main_no_compatdata(capsys):
    from shader_warmup.cli import main

    rc = main(["SomeGame"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_main_check_json_no_compatdata(capsys):
    from shader_warmup.cli import main

    rc = main(["SomeGame", "--json"])
    assert rc == 1
    captured = capsys.readouterr()
    assert '"ok": false' in captured.out
