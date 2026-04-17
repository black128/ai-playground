from __future__ import annotations

import curses
import time
from typing import List, Optional

from snake_game.engine import DOWN, GameConfig, LEFT, RIGHT, SnakeGame, TickResult, UP
from snake_game.storage import ScoreStorage

SNAKE_HEAD = "@"
SNAKE_BODY = "O"
EMPTY = " "
FOOD_GLYPHS = ("*", "+", "x", "+")

KEY_DIRECTIONS = {
    curses.KEY_UP: UP,
    curses.KEY_DOWN: DOWN,
    curses.KEY_LEFT: LEFT,
    curses.KEY_RIGHT: RIGHT,
    ord("w"): UP,
    ord("W"): UP,
    ord("s"): DOWN,
    ord("S"): DOWN,
    ord("a"): LEFT,
    ord("A"): LEFT,
    ord("d"): RIGHT,
    ord("D"): RIGHT,
}


def food_glyph(frame: int) -> str:
    return FOOD_GLYPHS[frame % len(FOOD_GLYPHS)]


def render_board(game: SnakeGame, frame: int = 0) -> List[str]:
    board = [[EMPTY for _ in range(game.width)] for _ in range(game.height)]

    if game.food is not None:
        food_x, food_y = game.food
        board[food_y][food_x] = food_glyph(frame)

    for index, (x, y) in enumerate(game.snake):
        board[y][x] = SNAKE_HEAD if index == 0 else SNAKE_BODY

    border = "+" + "-" * game.width + "+"
    lines = [border]
    lines.extend("|" + "".join(row) + "|" for row in board)
    lines.append(border)
    return lines


def direction_from_key(key: int) -> Optional[tuple[int, int]]:
    return KEY_DIRECTIONS.get(key)


class SnakeTerminalApp:
    FRAME_DELAY_MS = 50

    def __init__(self) -> None:
        self.game = SnakeGame(GameConfig(width=20, height=20, initial_length=3))
        self.score_storage = ScoreStorage()
        self.best_score = self.score_storage.load_best_score()
        self.running = False
        self.started = False
        self.animation_frame = 0
        self.level_banner_frames = 0
        self.next_tick_at = 0.0

    def run(self) -> None:
        curses.wrapper(self._main)

    def _main(self, stdscr: "curses._CursesWindow") -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.nodelay(True)
        stdscr.keypad(True)

        while True:
            stdscr.timeout(self.FRAME_DELAY_MS)
            key = stdscr.getch()
            should_quit = self._handle_key(key)
            if should_quit:
                break

            now = time.monotonic()
            if (
                self.started
                and self.running
                and not (self.game.game_over or self.game.won)
                and now >= self.next_tick_at
            ):
                result = self.game.tick()
                self._handle_tick_result(result)
                self.next_tick_at = now + (self.game.speed_ms / 1000)

            self.animation_frame += 1
            if self.level_banner_frames > 0:
                self.level_banner_frames -= 1
            self._draw(stdscr)

    def _handle_key(self, key: int) -> bool:
        if key == -1:
            return False
        if key in (ord("q"), ord("Q")):
            return True
        if key in (ord("r"), ord("R")):
            self.game.reset()
            self.running = False
            self.started = False
            self.level_banner_frames = 0
            return False
        if key in (ord("\n"), curses.KEY_ENTER, 10, 13):
            if not self.started or self.game.game_over or self.game.won:
                self.game.reset()
                self.started = True
                self.running = True
                self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
            return False
        if key in (ord("p"), ord("P"), ord(" ")):
            if self.started and not (self.game.game_over or self.game.won):
                self.running = not self.running
                if self.running:
                    self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
            return False

        direction = direction_from_key(key)
        if direction is not None:
            if not self.started:
                self.started = True
                self.running = True
                self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
            self.game.set_direction(direction)
        return False

    def _handle_tick_result(self, result: TickResult) -> None:
        if result.ate_food:
            self._persist_best_score()
        if result.level_up:
            self.level_banner_frames = 16
        if result.game_over or result.won:
            self.running = False
            self._persist_best_score()

    def _draw(self, stdscr: "curses._CursesWindow") -> None:
        stdscr.erase()
        board_lines = render_board(self.game, self.animation_frame)
        info_lines = [
            "Snake Arcade",
            (
                f"Score {self.game.score:04d} | Best {self.best_score:04d} | "
                f"Level {self.game.level} | Speed {self.game.speed_ms}ms"
            ),
            "Controls: Arrow keys / WASD move, Space pause, Enter start, R reset, Q quit",
        ]

        status = self._status_line()
        if status:
            info_lines.append(status)

        if self.level_banner_frames > 0:
            info_lines.append(f"Level Up! Welcome to level {self.game.level}.")

        required_height = len(info_lines) + len(board_lines) + 2
        required_width = max(len(line) for line in info_lines + board_lines)
        term_height, term_width = stdscr.getmaxyx()

        if term_height < required_height or term_width < required_width:
            stdscr.addstr(
                0,
                0,
                f"Terminal too small. Need at least {required_width}x{required_height}.",
            )
            stdscr.refresh()
            return

        row = 0
        for line in info_lines:
            stdscr.addstr(row, 0, line)
            row += 1

        row += 1
        for line in board_lines:
            stdscr.addstr(row, 0, line)
            row += 1

        stdscr.refresh()

    def _status_line(self) -> str:
        if not self.started:
            return "Status: Ready. Press an arrow key to launch the run."
        if self.game.won:
            return "Status: Board cleared. Press Enter or R for another run."
        if self.game.game_over:
            return "Status: Crash detected. Press Enter or R to restart."
        if not self.running:
            return "Status: Paused."

        foods_needed = self.game.config.foods_per_level - self.game.progress_to_next_level
        return (
            f"Status: Running. {foods_needed} more food"
            f"{'' if foods_needed == 1 else 's'} to level up."
        )

    def _persist_best_score(self) -> None:
        if self.game.score > self.best_score:
            self.best_score = self.score_storage.save_best_score(self.game.score)


def main() -> None:
    SnakeTerminalApp().run()


if __name__ == "__main__":
    main()
