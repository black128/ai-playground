from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from snake_game.storage import ScoreStorage


class ScoreStorageTests(unittest.TestCase):
    def test_missing_file_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = ScoreStorage(Path(tmp_dir) / "scores.json")
            self.assertEqual(storage.load_best_score(), 0)

    def test_save_best_score_persists_highest_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "scores.json"
            storage = ScoreStorage(path)

            self.assertEqual(storage.save_best_score(120), 120)
            self.assertEqual(storage.load_best_score(), 120)
            self.assertEqual(storage.save_best_score(90), 120)
            self.assertEqual(storage.load_best_score(), 120)

    def test_invalid_json_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "scores.json"
            path.write_text("{bad json", encoding="utf-8")

            storage = ScoreStorage(path)
            self.assertEqual(storage.load_best_score(), 0)


if __name__ == "__main__":
    unittest.main()
