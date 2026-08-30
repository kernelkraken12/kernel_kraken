"""Unit tests for gamesage (stdlib unittest — the 10/10 standard)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gamesage import rules, session, steam  # noqa: E402


class TestAcfParsing(unittest.TestCase):
    def test_parse_acf_basic(self):
        text = '''
"AppState"
{
    "appid" "1588550"
    "name" "Cairn"
    "StateFlags" "4"
}
'''
        data = steam.parse_acf(text)
        app = data.get("AppState", {})
        self.assertEqual(app.get("appid"), "1588550")
        self.assertEqual(app.get("name"), "Cairn")

    def test_parse_acf_empty(self):
        self.assertEqual(steam.parse_acf(""), {})


class TestFindAppid(unittest.TestCase):
    def test_digit_returns_int(self):
        self.assertEqual(steam.find_appid("1588550"), 1588550)

    def test_no_steam_returns_none(self):
        # no real steam install in the test env → None (or a digit path)
        with tempfile.TemporaryDirectory() as tmp:
            old = steam.STEAM_DIRS
            steam.STEAM_DIRS = [tmp]
            try:
                self.assertIsNone(steam.find_appid("nonexistent-game-xyz"))
            finally:
                steam.STEAM_DIRS = old


class TestShaderCache(unittest.TestCase):
    def test_missing_cache_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = steam.STEAM_DIRS
            steam.STEAM_DIRS = [tmp]
            try:
                self.assertEqual(steam.shader_cache_size(999999), 0)
            finally:
                steam.STEAM_DIRS = old

    def test_cache_size_counts_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "steamapps" / "shadercache" / "123"
            root.mkdir(parents=True)
            (root / "a.dxvk-cache").write_bytes(b"x" * 2048)
            old = steam.STEAM_DIRS
            steam.STEAM_DIRS = [tmp]
            try:
                self.assertEqual(steam.shader_cache_size(123), 2048)
            finally:
                steam.STEAM_DIRS = old


class TestRules(unittest.TestCase):
    def test_no_data_no_crash(self):
        recs = rules.recommend({})
        self.assertIsInstance(recs, list)

    def test_low_fps_high_priority(self):
        recs = rules.recommend({"avg_fps": 22, "peak_gpu": 60, "mangohud_present": True})
        self.assertTrue(any(r["level"] == "high" for r in recs))

    def test_hot_gpu_rule(self):
        recs = rules.recommend({"peak_gpu": 88, "mangohud_present": True})
        self.assertTrue(any("hot" in r["text"] for r in recs))

    def test_game_specific_tip(self):
        recs = rules.recommend({"game": "Cairn", "mangohud_present": True})
        self.assertTrue(any("Cairn" in r["text"] for r in recs))

    def test_smooth_session_no_recs(self):
        recs = rules.recommend({"avg_fps": 120, "peak_gpu": 50, "peak_cpu": 20,
                                "mangohud_present": True, "shader_bytes": 50_000_000})
        self.assertEqual(recs, [])


class TestSessionStore(unittest.TestCase):
    def test_start_end_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = session.state_dir
            session.state_dir = lambda: Path(tmp)
            try:
                sess = session.start_session("Test Game", 123)
                self.assertEqual(sess["game"], "Test Game")
                self.assertEqual(sess["appid"], 123)
                loaded = session.load_session(sess["id"])
                self.assertEqual(loaded["game"], "Test Game")
                ended = session.end_session(sess["id"])
                self.assertIsNotNone(ended["ended"])
            finally:
                session.state_dir = old

    def test_no_session_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = session.state_dir
            session.state_dir = lambda: Path(tmp)
            try:
                self.assertIsNone(session.load_session("does-not-exist"))
            finally:
                session.state_dir = old


class TestRecommendIntegration(unittest.TestCase):
    def test_stats_build(self):
        from gamesage import report
        sess = {
            "game": "Cairn",
            "appid": 1588550,
            "started": "2026-08-30 10:00:00",
            "ended": "2026-08-30 11:00:00",
            "samples": [
                {"time": "10:00:00", "temps": {"amdgpu:temp1": 66.0}, "load": 3.5},
                {"time": "10:00:20", "temps": {"amdgpu:temp1": 71.0}, "load": 4.2},
            ],
        }
        stats = report.build_stats(sess, {"cpu_count": 8})
        self.assertEqual(stats["game"], "Cairn")
        self.assertEqual(stats["duration"], "1h 00m")
        self.assertEqual(stats["peak_gpu"], 71.0)
        self.assertIsNotNone(stats["peak_cpu_pct"])


class TestCliHelp(unittest.TestCase):
    def test_version(self):
        from gamesage import cli
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
