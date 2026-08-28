"""Unit tests for the protondbcli package (stdlib unittest — runs anywhere)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# make the package importable from the repo layout (src/protondbcli)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from protondbcli import api, cache, output  # noqa: E402
from protondbcli.tux import TUX_V2, tux_banner  # noqa: E402


class TestTierMapping(unittest.TestCase):
    def test_build_result_platinum(self):
        summary = {"bestReportedTier": "platinum", "confidence": "strong", "score": 0.76, "total": 81}
        r = api.build_result(1588550, "Cairn", summary)
        self.assertEqual(r.tier, "platinum")
        self.assertEqual(r.confidence, "strong")
        self.assertEqual(r.total_reports, 81)
        self.assertEqual(r.source, "live")

    def test_build_result_unknown_tier_falls_back(self):
        summary = {"bestReportedTier": "not-a-tier", "confidence": "weak", "total": 3}
        r = api.build_result(1, "X", summary)
        self.assertEqual(r.tier, "pending")

    def test_tier_icon(self):
        self.assertEqual(api.tier_icon("platinum"), "🏆")
        self.assertEqual(api.tier_icon("borked"), "💀")
        self.assertEqual(api.tier_icon("weird"), "❓")


class TestSteamSearch(unittest.TestCase):
    @mock.patch("protondbcli.api._http_get_json")
    def test_search_steam_parses(self, mock_get):
        mock_get.return_value = {
            "items": [
                {"name": "Cairn", "id": 1588550, "type": "app"},
                {"name": "Cairn - Deluxe", "id": 4031100, "type": "app"},
            ]
        }
        results = api.search_steam("cairn")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["appid"], 1588550)
        self.assertEqual(results[0]["name"], "Cairn")

    @mock.patch("protondbcli.api._http_get_json")
    def test_search_steam_empty(self, mock_get):
        mock_get.return_value = {"items": []}
        self.assertEqual(api.search_steam("zzz-no-such-game"), [])


class TestCache(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_env = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()
        if self._old_env is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = self._old_env

    def test_cache_roundtrip(self):
        cache.write_cache(1588550, {"bestReportedTier": "platinum"})
        got = cache.read_cache(1588550)
        self.assertEqual(got["bestReportedTier"], "platinum")

    def test_cache_miss(self):
        self.assertIsNone(cache.read_cache(99999999))

    def test_cache_expiry(self):
        cache.write_cache(1, {"x": 1})
        path = cache._cache_path(1)
        # fake an old timestamp
        import json
        data = json.loads(path.read_text())
        data["_fetched_at"] = 0
        path.write_text(json.dumps(data))
        self.assertIsNone(cache.read_cache(1))


class TestOutput(unittest.TestCase):
    def test_render_contains_key_sections(self):
        summary = {"bestReportedTier": "platinum", "confidence": "strong", "total": 81}
        r = api.build_result(1588550, "Cairn", summary)
        text = output.render_result(r, show_banner=True)
        self.assertIn("CAIRN", text)
        self.assertIn("CONFIRMED FIXES", text)
        self.assertIn("HOW TO RUN", text)
        self.assertIn("gamemoderun %command%", text)
        self.assertIn("1588550", text)

    def test_tux_banner_contains_penguin(self):
        self.assertIn("o_o", TUX_V2)
        banner = tux_banner(color=False)
        self.assertIn("TUX APPROVES", banner)


if __name__ == "__main__":
    unittest.main()
