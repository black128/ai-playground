from __future__ import annotations

import tkinter as tk

from snake_game.engine import DIRECTIONS, GameConfig, SnakeGame


class SnakeApp:
    CELL_SIZE = 24
    UPDATE_DELAY_MS = 140
    BG_COLOR = "#f4efe6"
    BOARD_BORDER_COLOR = "#5b4636"
    GRID_LIGHT_COLOR = "#efe4c8"
    GRID_DARK_COLOR = "#dfcf9f"
    SNAKE_HEAD_COLOR = "#1f7a3d"
    SNAKE_BODY_COLOR = "#39a357"
    FOOD_COLOR = "#d62828"
    TEXT_COLOR = "#2f241d"

    def __init__(self) -> None:
        self.game = SnakeGame(GameConfig(width=20, height=20, initial_length=3))
        self.running = True

        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.root.resizable(False, False)

        canvas_width = self.game.width * self.CELL_SIZE
        canvas_height = self.game.height * self.CELL_SIZE

        self.status_var = tk.StringVar()

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg=self.GRID_LIGHT_COLOR,
            highlightthickness=4,
            highlightbackground=self.BOARD_BORDER_COLOR,
        )
        self.canvas.pack(padx=12, pady=(12, 6))

        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 12),
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            padx=12,
            pady=8,
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 12))

        self.root.configure(bg=self.BG_COLOR)
        self.root.bind("<KeyPress>", self._handle_keypress)
        self._show_window()

        self._draw()
        self._schedule_next_tick()

    def run(self) -> None:
        self.root.mainloop()

    def _handle_keypress(self, event: tk.Event) -> None:
        if event.keysym in DIRECTIONS:
            self.game.change_direction_by_key(event.keysym)
        elif event.keysym.lower() == "r":
            self.game.reset()
            self.running = True
            self._draw()
            self._schedule_next_tick()
        elif event.keysym == "space":
            self.running = not self.running
            self._draw()
            if self.running and not (self.game.game_over or self.game.won):
                self._schedule_next_tick()

    def _show_window(self) -> None:
        window_width = self.game.width * self.CELL_SIZE + 24
        window_height = self.game.height * self.CELL_SIZE + 72
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        pos_x = max((screen_width - window_width) // 2, 0)
        pos_y = max((screen_height - window_height) // 2, 0)
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.root.update_idletasks()
        self.root.lift()
        self.root.focus_force()
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))

    def _schedule_next_tick(self) -> None:
        self.root.after(self.UPDATE_DELAY_MS, self._game_loop)

    def _game_loop(self) -> None:
        if not self.running:
            self._draw()
            return
        if self.game.game_over or self.game.won:
            self._draw()
            return

        self.game.tick()
        self._draw()

        if self.running and not (self.game.game_over or self.game.won):
            self._schedule_next_tick()

    def _draw(self) -> None:
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_food()
        self._draw_snake()
        self._update_status()

    def _draw_grid(self) -> None:
        for x in range(self.game.width):
            for y in range(self.game.height):
                color = (
                    self.GRID_LIGHT_COLOR if (x + y) % 2 == 0 else self.GRID_DARK_COLOR
                )
                self._draw_cell(
                    x,
                    y,
                    color,
                    inset=0,
                    outline=self.BOARD_BORDER_COLOR,
                    outline_width=1,
                )

    def _draw_food(self) -> None:
        if self.game.food is None:
            return
        food_x, food_y = self.game.food
        self._draw_cell(
            food_x,
            food_y,
            self.FOOD_COLOR,
            inset=5,
            outline="#7f1d1d",
            outline_width=2,
        )

    def _draw_snake(self) -> None:
        for index, (x, y) in enumerate(self.game.snake):
            color = self.SNAKE_HEAD_COLOR if index == 0 else self.SNAKE_BODY_COLOR
            outline = "#14532d" if index == 0 else "#166534"
            self._draw_cell(x, y, color, inset=2, outline=outline, outline_width=2)

    def _draw_cell(
        self,
        x: int,
        y: int,
        color: str,
        inset: int = 1,
        outline: str = "",
        outline_width: int = 1,
    ) -> None:
        left = x * self.CELL_SIZE + inset
        top = y * self.CELL_SIZE + inset
        right = (x + 1) * self.CELL_SIZE - inset
        bottom = (y + 1) * self.CELL_SIZE - inset
        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=color,
            outline=outline,
            width=outline_width,
        )

    def _update_status(self) -> None:
        if self.game.won:
            status = (
                f"Score: {self.game.score} | You win! Press R to restart."
            )
        elif self.game.game_over:
            status = (
                f"Score: {self.game.score} | Game over! Press R to restart."
            )
        elif not self.running:
            status = f"Score: {self.game.score} | Paused. Press Space to continue."
        else:
            status = (
                f"Score: {self.game.score} | Arrow keys to move, Space to pause, R to restart."
            )
        self.status_var.set(status)


def main() -> None:
    app = SnakeApp()
    app.run()


if __name__ == "__main__":
    main()
