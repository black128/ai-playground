import curses
import unittest

from snake_game.engine import GameConfig, SnakeGame
from snake_game.terminal_app import direction_from_key, render_board


class SnakeTerminalAppTests(unittest.TestCase):
    def test_render_board_draws_border_snake_and_food(self) -> None:
        game = SnakeGame(GameConfig(width=5, height=4, initial_length=3, random_seed=1))
        game.snake = [(2, 1), (1, 1), (0, 1)]
        game.food = (4, 3)

        lines = render_board(game)

        self.assertEqual(lines[0], "+-----+")
        self.assertEqual(lines[-1], "+-----+")
        self.assertIn("@", lines[2])
        self.assertIn("O", lines[2])
        self.assertEqual(lines[4], "|    *|")

    def test_render_board_exact_layout(self) -> None:
        game = SnakeGame(GameConfig(width=5, height=4, initial_length=3, random_seed=1))
        game.snake = [(2, 1), (1, 1), (0, 1)]
        game.food = (4, 3)

        lines = render_board(game)

        self.assertEqual(
            lines,
            [
                "+-----+",
                "|     |",
                "|OO@  |",
                "|     |",
                "|    *|",
                "+-----+",
            ],
        )

    def test_direction_from_key_supports_arrows_and_wasd(self) -> None:
        self.assertEqual(direction_from_key(curses.KEY_UP), (0, -1))
        self.assertEqual(direction_from_key(ord("a")), (-1, 0))
        self.assertIsNone(direction_from_key(ord("x")))


if __name__ == "__main__":
    unittest.main()
