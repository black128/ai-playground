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


@dataclass
class SnakeGame:
    config: GameConfig = field(default_factory=GameConfig)
    score: int = 0
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

    def reset(self) -> None:
        if self.config.initial_length < 2:
            raise ValueError("initial_length must be at least 2")
        if self.config.initial_length > self.config.width:
            raise ValueError("initial_length cannot exceed board width")

        start_x = self.config.initial_length + 1
        start_y = self.config.height // 2
        self.direction = RIGHT
        self.score = 0
        self.game_over = False
        self.won = False
        self.snake = [
            (start_x - offset, start_y) for offset in range(self.config.initial_length)
        ]
        self.food = self._spawn_food()

    def set_direction(self, new_direction: Position) -> None:
        if self.game_over or self.won:
            return
        if new_direction == OPPOSITES[self.direction]:
            return
        self.direction = new_direction

    def change_direction_by_key(self, key: str) -> None:
        if key in DIRECTIONS:
            self.set_direction(DIRECTIONS[key])

    def tick(self) -> None:
        if self.game_over or self.won:
            return

        next_head = self._next_head_position()
        grow = next_head == self.food
        body_to_check: Sequence[Position]
        if grow:
            body_to_check = self.snake
        else:
            body_to_check = self.snake[:-1]

        if not self._is_inside_board(next_head) or next_head in body_to_check:
            self.game_over = True
            return

        self.snake.insert(0, next_head)
        if grow:
            self.score += 1
            self.food = self._spawn_food()
            if self.food is None:
                self.won = True
        else:
            self.snake.pop()

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

