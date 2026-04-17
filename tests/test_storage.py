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

    def test_record_run_builds_sorted_leaderboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = ScoreStorage(Path(tmp_dir) / "scores.json")

            storage.record_run(
                score=90,
                difficulty="arcade",
                level=4,
                foods_eaten=9,
                steps=40,
            )
            storage.record_run(
                score=140,
                difficulty="expert",
                level=5,
                foods_eaten=11,
                steps=52,
            )
            storage.record_run(
                score=110,
                difficulty="arcade",
                level=4,
                foods_eaten=10,
                steps=47,
            )

            leaderboard = storage.load_leaderboard(limit=3)
            arcade_only = storage.load_leaderboard(difficulty="arcade", limit=5)

            self.assertEqual([entry.score for entry in leaderboard], [140, 110, 90])
            self.assertEqual([entry.score for entry in arcade_only], [110, 90])
            self.assertEqual(storage.load_best_score(), 140)


if __name__ == "__main__":
    unittest.main()
