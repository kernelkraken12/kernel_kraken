"""Unit tests for shaderwarm (stdlib unittest — runs anywhere)."""

import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shaderwarm import cache, output, steam  # noqa: E402
from shaderwarm.output import TUX  # noqa: E402


def make_fake_steam(root: Path, games: dict[int, str]) -> Path:
    """Build a real-shaped fake Steam tree for tests."""
    steamapps = root / "steamapps"
    steamapps.mkdir(parents=True)
    # libraryfolders.vdf (real Valve KeyValue)
    (steamapps / "libraryfolders.vdf").write_text(
        '"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}\n' % root,
        encoding="utf-8",
    )
    for appid, name in games.items():
        (steamapps / f"appmanifest_{appid}.acf").write_text(
            f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t"{name}"\n}}\n',
            encoding="utf-8",
        )
    return steamapps


class TestSteamDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Steam"
        make_fake_steam(self.root, {1588550: "Cairn", 123456: "Some Game"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_root_override(self):
        self.assertEqual(steam.find_steam_root(str(self.root)), self.root)

    def test_scan_games_parses_acf(self):
        games = steam.scan_games(self.root)
        names = {g.name for g in games}
        self.assertIn("Cairn", names)
        self.assertIn("Some Game", names)
        cairn = next(g for g in games if g.name == "Cairn")
        self.assertEqual(cairn.appid, 1588550)

    def test_shader_cache_dir(self):
        game = steam.SteamGame(appid=1588550, name="Cairn", root=self.root)
        self.assertEqual(
            steam.shader_cache_dir(game),
            self.root / "steamapps" / "shadercache" / "1588550",
        )


class TestCacheInspection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Steam"
        make_fake_steam(self.root, {1588550: "Cairn"})
        self.game = steam.SteamGame(appid=1588550, name="Cairn", root=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_cache(self, size_mb: int = 30):
        d = steam.shader_cache_dir(self.game)
        d.mkdir(parents=True)
        (d / "Cairn.dxvk-cache").write_bytes(b"\x00" * (size_mb * 1_000_000))

    def test_cold_when_missing(self):
        info = cache.inspect(self.game)
        self.assertEqual(info.state, "cold")
        self.assertFalse(info.exists)

    def test_warm_when_large(self):
        self._make_cache(30)
        info = cache.inspect(self.game)
        self.assertEqual(info.state, "warm")
        self.assertTrue(info.size_bytes >= 30_000_000)

    def test_cold_ish_when_tiny(self):
        self._make_cache(1)
        info = cache.inspect(self.game)
        self.assertEqual(info.state, "cold-ish")

    def test_backup_roundtrip(self):
        self._make_cache(5)
        dest = Path(self.tmp.name) / "backups"
        out = cache.backup(self.game, dest)
        self.assertIsNotNone(out)
        with tarfile.open(out) as tf:
            names = tf.getnames()
        self.assertTrue(any("shadercache-1588550" in n for n in names))

    def test_clear(self):
        self._make_cache(5)
        self.assertTrue(cache.clear(self.game))
        self.assertFalse(steam.shader_cache_dir(self.game).exists())


class TestOutput(unittest.TestCase):
    def test_tux_present(self):
        self.assertIn("o_o", TUX)
        self.assertIn("TUX WARMS", output.banner())

    def test_render_status_warm(self):
        info = cache.CacheInfo(
            game=steam.SteamGame(1588550, "Cairn", Path("/tmp")),
            exists=True, size_bytes=30_000_000, file_count=3,
            newest_mtime=0, state="warm",
        )
        text = output.render_status(info)
        self.assertIn("Cairn", text)
        self.assertIn("warm", text)


if __name__ == "__main__":
    unittest.main()
