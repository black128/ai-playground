import unittest

from snake_game.app import BrowserSnakeController


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


if __name__ == "__main__":
    unittest.main()
