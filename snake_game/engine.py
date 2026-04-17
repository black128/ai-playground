from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional, Sequence, Tuple

Position = Tuple[int, int]

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

DIRECTIONS: Dict[str, Position] = {
    "Up": UP,
    "Down": DOWN,
    "Left": LEFT,
    "Right": RIGHT,
}

OPPOSITES = {
    UP: DOWN,
    DOWN: UP,
    LEFT: RIGHT,
    RIGHT: LEFT,
}


@dataclass
class GameConfig:
    width: int = 20
    height: int = 20
    initial_length: int = 3
    random_seed: Optional[int] = None
    points_per_food: int = 10
    foods_per_level: int = 4
    base_speed_ms: int = 180
    speed_step_ms: int = 12
    min_speed_ms: int = 72


@dataclass(frozen=True)
class TickResult:
    moved: bool
    ate_food: bool
    game_over: bool
    won: bool
    level_up: bool
    score: int
    level: int
    consumed_food_position: Optional[Position] = None


@dataclass
class SnakeGame:
    config: GameConfig = field(default_factory=GameConfig)
    score: int = 0
    foods_eaten: int = 0
    steps: int = 0
    game_over: bool = False
    won: bool = False
    direction: Position = RIGHT
    snake: List[Position] = field(default_factory=list)
    food: Optional[Position] = None

    def __post_init__(self) -> None:
        self._rng = random.Random(self.config.random_seed)
        self.reset()

    @property
    def width(self) -> int:
        return self.config.width

    @property
    def height(self) -> int:
        return self.config.height

    @property
    def level(self) -> int:
        return 1 + (self.foods_eaten // self.config.foods_per_level)

    @property
    def speed_ms(self) -> int:
        reduction = (self.level - 1) * self.config.speed_step_ms
        return max(self.config.min_speed_ms, self.config.base_speed_ms - reduction)

    @property
    def progress_to_next_level(self) -> int:
        return self.foods_eaten % self.config.foods_per_level

    def reset(self) -> None:
        if self.config.initial_length < 2:
            raise ValueError("initial_length must be at least 2")
        if self.config.initial_length > self.config.width:
            raise ValueError("initial_length cannot exceed board width")
        if self.config.foods_per_level < 1:
            raise ValueError("foods_per_level must be at least 1")
        if self.config.points_per_food < 1:
            raise ValueError("points_per_food must be at least 1")
        if self.config.min_speed_ms < 20:
            raise ValueError("min_speed_ms must be at least 20")
        if self.config.base_speed_ms < self.config.min_speed_ms:
            raise ValueError("base_speed_ms cannot be lower than min_speed_ms")
        if self.config.speed_step_ms < 0:
            raise ValueError("speed_step_ms cannot be negative")

        start_x = self.config.initial_length + 1
        start_y = self.config.height // 2
        self.direction = RIGHT
        self.score = 0
        self.foods_eaten = 0
        self.steps = 0
        self.game_over = False
        self.won = False
        self.snake = [
            (start_x - offset, start_y) for offset in range(self.config.initial_length)
        ]
        self.food = self._spawn_food()

    def set_direction(self, new_direction: Position) -> bool:
        if self.game_over or self.won:
            return False
        if new_direction == OPPOSITES[self.direction]:
            return False
        if new_direction == self.direction:
            return False
        self.direction = new_direction
        return True

    def change_direction_by_key(self, key: str) -> bool:
        if key in DIRECTIONS:
            return self.set_direction(DIRECTIONS[key])
        return False

    def tick(self) -> TickResult:
        if self.game_over or self.won:
            return TickResult(
                moved=False,
                ate_food=False,
                game_over=self.game_over,
                won=self.won,
                level_up=False,
                score=self.score,
                level=self.level,
            )

        previous_level = self.level
        next_head = self._next_head_position()
        grow = next_head == self.food
        body_to_check: Sequence[Position]
        if grow:
            body_to_check = self.snake
        else:
            body_to_check = self.snake[:-1]

        if not self._is_inside_board(next_head) or next_head in body_to_check:
            self.game_over = True
            return TickResult(
                moved=False,
                ate_food=False,
                game_over=True,
                won=False,
                level_up=False,
                score=self.score,
                level=self.level,
            )

        self.snake.insert(0, next_head)
        self.steps += 1
        if grow:
            self.score += self.config.points_per_food
            self.foods_eaten += 1
            self.food = self._spawn_food()
            if self.food is None:
                self.won = True
        else:
            self.snake.pop()

        current_level = self.level
        return TickResult(
            moved=True,
            ate_food=grow,
            game_over=self.game_over,
            won=self.won,
            level_up=current_level > previous_level,
            score=self.score,
            level=current_level,
            consumed_food_position=next_head if grow else None,
        )

    def _next_head_position(self) -> Position:
        head_x, head_y = self.snake[0]
        delta_x, delta_y = self.direction
        return (head_x + delta_x, head_y + delta_y)

    def _is_inside_board(self, position: Position) -> bool:
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def _spawn_food(self) -> Optional[Position]:
        available_positions = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.snake
        ]
        if not available_positions:
            return None
        return self._rng.choice(available_positions)
