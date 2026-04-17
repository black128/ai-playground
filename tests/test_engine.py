import unittest

from snake_game.engine import DOWN, GameConfig, LEFT, RIGHT, SnakeGame, UP


class SnakeGameTests(unittest.TestCase):
    def test_reset_initializes_snake_and_food(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))

        self.assertEqual(game.snake, [(4, 5), (3, 5), (2, 5)])
        self.assertIsNotNone(game.food)
        self.assertNotIn(game.food, game.snake)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.level, 1)
        self.assertEqual(game.speed_ms, 180)
        self.assertFalse(game.game_over)

    def test_tick_moves_snake_forward(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))
        game.food = (0, 0)

        game.tick()

        self.assertEqual(game.snake, [(5, 5), (4, 5), (3, 5)])
        self.assertEqual(game.score, 0)
        self.assertEqual(game.steps, 1)

    def test_eating_food_increases_score_and_length(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))
        game.food = (5, 5)

        result = game.tick()

        self.assertEqual(game.snake, [(5, 5), (4, 5), (3, 5), (2, 5)])
        self.assertEqual(game.score, 10)
        self.assertEqual(game.foods_eaten, 1)
        self.assertTrue(result.ate_food)
        self.assertIsNotNone(game.food)
        self.assertNotIn(game.food, game.snake)

    def test_reverse_direction_is_ignored(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))

        game.set_direction(LEFT)

        self.assertEqual(game.direction, RIGHT)

    def test_valid_direction_change_is_applied(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))

        game.set_direction(UP)

        self.assertEqual(game.direction, UP)

    def test_wall_collision_sets_game_over(self) -> None:
        game = SnakeGame(GameConfig(width=6, height=6, initial_length=3, random_seed=1))
        game.food = (0, 0)

        game.tick()
        game.tick()

        self.assertTrue(game.game_over)

    def test_self_collision_sets_game_over(self) -> None:
        game = SnakeGame(GameConfig(width=6, height=6, initial_length=3, random_seed=1))
        game.snake = [(3, 3), (3, 4), (2, 4), (2, 3)]
        game.direction = DOWN
        game.food = (0, 0)

        game.tick()
        game.set_direction(LEFT)
        game.tick()
        game.set_direction(UP)
        game.tick()

        self.assertTrue(game.game_over)

    def test_moving_into_old_tail_position_is_allowed(self) -> None:
        game = SnakeGame(GameConfig(width=6, height=6, initial_length=3, random_seed=1))
        game.snake = [(2, 2), (2, 3), (1, 3), (1, 2)]
        game.direction = LEFT
        game.food = (0, 0)

        game.tick()

        self.assertFalse(game.game_over)
        self.assertEqual(game.snake, [(1, 2), (2, 2), (2, 3), (1, 3)])

    def test_win_when_board_is_filled(self) -> None:
        game = SnakeGame(GameConfig(width=2, height=2, initial_length=2, random_seed=1))
        game.snake = [(1, 0), (0, 0), (0, 1)]
        game.direction = DOWN
        game.food = (1, 1)

        game.tick()

        self.assertTrue(game.won)
        self.assertFalse(game.game_over)
        self.assertIsNone(game.food)
        self.assertEqual(len(game.snake), 4)

    def test_reset_restarts_game_state(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))
        game.food = (5, 5)
        game.tick()
        game.tick()

        game.reset()

        self.assertEqual(game.score, 0)
        self.assertFalse(game.game_over)
        self.assertFalse(game.won)
        self.assertEqual(game.direction, RIGHT)
        self.assertEqual(len(game.snake), 3)
        self.assertEqual(game.level, 1)
        self.assertEqual(game.steps, 0)

    def test_invalid_initial_length_raises(self) -> None:
        with self.assertRaises(ValueError):
            SnakeGame(GameConfig(width=3, height=3, initial_length=4))

    def test_level_increases_and_speed_gets_faster(self) -> None:
        game = SnakeGame(
            GameConfig(
                width=10,
                height=10,
                initial_length=3,
                random_seed=1,
                foods_per_level=2,
                speed_step_ms=15,
            )
        )

        game.food = (5, 5)
        first_result = game.tick()
        game.food = (6, 5)
        second_result = game.tick()

        self.assertEqual(game.level, 2)
        self.assertEqual(game.score, 20)
        self.assertFalse(first_result.level_up)
        self.assertTrue(second_result.level_up)
        self.assertEqual(game.speed_ms, 165)

    def test_speed_respects_minimum_value(self) -> None:
        game = SnakeGame(
            GameConfig(
                width=10,
                height=10,
                initial_length=3,
                random_seed=1,
                foods_per_level=1,
                base_speed_ms=120,
                speed_step_ms=30,
                min_speed_ms=60,
            )
        )

        game.foods_eaten = 6

        self.assertEqual(game.level, 7)
        self.assertEqual(game.speed_ms, 60)

    def test_invalid_speed_configuration_raises(self) -> None:
        with self.assertRaises(ValueError):
            SnakeGame(GameConfig(base_speed_ms=50, min_speed_ms=60))

    def test_change_direction_by_key(self) -> None:
        game = SnakeGame(GameConfig(width=10, height=10, initial_length=3, random_seed=1))

        game.change_direction_by_key("Up")

        self.assertEqual(game.direction, UP)


if __name__ == "__main__":
    unittest.main()
