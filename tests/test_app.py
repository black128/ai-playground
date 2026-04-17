from pathlib import Path
import tempfile
import unittest

from snake_game.app import BrowserSnakeController
from snake_game.storage import ScoreStorage


class BrowserSnakeControllerTests(unittest.TestCase):
    def test_start_and_direction_begin_run(self) -> None:
        controller = BrowserSnakeController()

        state = controller.handle_action("direction", {"key": "ArrowUp"})

        self.assertTrue(state["started"])
        self.assertTrue(state["running"])
        self.assertEqual(state["direction"], "Up")

    def test_reset_restores_ready_state(self) -> None:
        controller = BrowserSnakeController()
        controller.handle_action("direction", {"key": "ArrowUp"})

        state = controller.handle_action("reset", {})

        self.assertFalse(state["started"])
        self.assertFalse(state["running"])
        self.assertEqual(state["score"], 0)
        self.assertEqual(state["level"], 1)

    def test_set_difficulty_updates_selected_profile(self) -> None:
        controller = BrowserSnakeController()

        state = controller.handle_action("set_difficulty", {"difficulty": "expert"})

        self.assertEqual(state["selected_difficulty"], "expert")
        self.assertEqual(state["speed_ms"], 150)
        self.assertEqual(state["foods_per_level"], 3)

    def test_state_includes_current_difficulty_leaderboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = ScoreStorage(Path(tmp_dir) / "scores.json")
            storage.record_run(
                score=160,
                difficulty="expert",
                level=6,
                foods_eaten=13,
                steps=58,
            )
            storage.record_run(
                score=90,
                difficulty="arcade",
                level=4,
                foods_eaten=9,
                steps=44,
            )

            controller = BrowserSnakeController(storage=storage, initial_difficulty="expert")
            state = controller.get_state()

            self.assertEqual(state["selected_difficulty"], "expert")
            self.assertEqual(len(state["leaderboard_current"]), 1)
            self.assertEqual(state["leaderboard_current"][0]["score"], 160)


if __name__ == "__main__":
    unittest.main()
