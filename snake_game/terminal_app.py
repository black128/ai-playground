from __future__ import annotations

import curses
from typing import List, Optional

from snake_game.engine import DOWN, GameConfig, LEFT, RIGHT, SnakeGame, UP

SNAKE_HEAD = "@"
SNAKE_BODY = "O"
FOOD = "*"
EMPTY = " "

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


def render_board(game: SnakeGame) -> List[str]:
    board = [[EMPTY for _ in range(game.width)] for _ in range(game.height)]

    if game.food is not None:
        food_x, food_y = game.food
        board[food_y][food_x] = FOOD

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
    UPDATE_DELAY_MS = 140

    def __init__(self) -> None:
        self.game = SnakeGame(GameConfig(width=20, height=20, initial_length=3))
        self.running = True

    def run(self) -> None:
        curses.wrapper(self._main)

    def _main(self, stdscr: "curses._CursesWindow") -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.nodelay(True)
        stdscr.timeout(self.UPDATE_DELAY_MS)
        stdscr.keypad(True)

        while True:
            self._draw(stdscr)
            key = stdscr.getch()
            should_quit = self._handle_key(key)
            if should_quit:
                break

            if self.running and not (self.game.game_over or self.game.won):
                self.game.tick()

    def _handle_key(self, key: int) -> bool:
        if key == -1:
            return False
        if key in (ord("q"), ord("Q")):
            return True
        if key in (ord("p"), ord("P"), ord(" ")):
            self.running = not self.running
            return False
        if key in (ord("r"), ord("R")):
            self.game.reset()
            self.running = True
            return False

        direction = direction_from_key(key)
        if direction is not None:
            self.game.set_direction(direction)
        return False

    def _draw(self, stdscr: "curses._CursesWindow") -> None:
        stdscr.erase()
        board_lines = render_board(self.game)

        info_lines = [
            f"Snake Game | Score: {self.game.score}",
            "Controls: Arrow keys / WASD move, P or Space pause, R restart, Q quit",
        ]

        if self.game.won:
            info_lines.append("Status: You win!")
        elif self.game.game_over:
            info_lines.append("Status: Game over!")
        elif self.running:
            info_lines.append("Status: Running")
        else:
            info_lines.append("Status: Paused")

        required_height = len(info_lines) + len(board_lines) + 1
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


def main() -> None:
    SnakeTerminalApp().run()


if __name__ == "__main__":
    main()
