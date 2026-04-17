from __future__ import annotations

import math
import tkinter as tk

from snake_game.engine import (
    DIRECTIONS,
    DOWN,
    GameConfig,
    LEFT,
    RIGHT,
    SnakeGame,
    TickResult,
    UP,
)
from snake_game.storage import ScoreStorage


class SnakeApp:
    CELL_SIZE = 24
    FRAME_DELAY_MS = 33
    BG_COLOR = "#101418"
    PANEL_COLOR = "#172128"
    PANEL_ALT_COLOR = "#22313b"
    BOARD_BORDER_COLOR = "#78c8b4"
    GRID_LIGHT_COLOR = "#132027"
    GRID_DARK_COLOR = "#0d181e"
    SNAKE_HEAD_COLOR = "#8ff76d"
    SNAKE_BODY_START = "#3dcf75"
    SNAKE_BODY_END = "#176f56"
    FOOD_COLOR = "#ff7b6b"
    FOOD_CORE_COLOR = "#ffe4a8"
    TEXT_COLOR = "#edf8f5"
    MUTED_TEXT_COLOR = "#9cb5ae"
    OVERLAY_COLOR = "#081014"
    BANNER_COLOR = "#f7c948"

    KEY_ALIASES = {
        "w": "Up",
        "W": "Up",
        "a": "Left",
        "A": "Left",
        "s": "Down",
        "S": "Down",
        "d": "Right",
        "D": "Right",
    }

    def __init__(self) -> None:
        self.game = SnakeGame(GameConfig(width=20, height=20, initial_length=3))
        self.score_storage = ScoreStorage()
        self.best_score = self.score_storage.load_best_score()
        self.running = False
        self.started = False
        self.animation_frame = 0
        self.level_banner_frames = 0
        self.food_flash_frames = 0
        self.particles: list[dict[str, float]] = []
        self.logic_job: str | None = None
        self.render_job: str | None = None

        self.root = tk.Tk()
        self.root.title("Snake Arcade")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        board_width = self.game.width * self.CELL_SIZE
        board_height = self.game.height * self.CELL_SIZE

        self.title_var = tk.StringVar(value="Snake Arcade")
        self.stats_var = tk.StringVar()
        self.footer_var = tk.StringVar()

        top_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        top_frame.pack(fill="x", padx=18, pady=(18, 10))

        self.title_label = tk.Label(
            top_frame,
            textvariable=self.title_var,
            font=("Helvetica", 22, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.BG_COLOR,
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.stats_label = tk.Label(
            top_frame,
            textvariable=self.stats_var,
            font=("Helvetica", 11, "bold"),
            fg=self.MUTED_TEXT_COLOR,
            bg=self.BG_COLOR,
            anchor="w",
            pady=4,
        )
        self.stats_label.pack(fill="x")

        self.canvas = tk.Canvas(
            self.root,
            width=board_width,
            height=board_height,
            bg=self.GRID_DARK_COLOR,
            highlightthickness=3,
            highlightbackground=self.BOARD_BORDER_COLOR,
        )
        self.canvas.pack(padx=18, pady=0)

        self.footer_label = tk.Label(
            self.root,
            textvariable=self.footer_var,
            font=("Helvetica", 11),
            fg=self.TEXT_COLOR,
            bg=self.PANEL_COLOR,
            anchor="w",
            padx=16,
            pady=10,
        )
        self.footer_label.pack(fill="x", padx=18, pady=(10, 18))

        self.root.bind("<KeyPress>", self._handle_keypress)
        self._show_window()
        self._draw()
        self._schedule_render()

    def run(self) -> None:
        self.root.mainloop()

    def _handle_keypress(self, event: tk.Event) -> None:
        keysym = self.KEY_ALIASES.get(event.keysym, event.keysym)
        if keysym in DIRECTIONS:
            if not self.started:
                self.started = True
                self.running = True
            self.game.change_direction_by_key(keysym)
            self._schedule_logic_tick()
            return

        if event.keysym in ("Return", "KP_Enter"):
            if not self.started or self.game.game_over or self.game.won:
                self._reset_game()
                self.started = True
                self.running = True
                self._schedule_logic_tick()
            return

        if event.keysym.lower() == "r":
            self._reset_game()
            return

        if event.keysym == "space" and self.started and not (self.game.game_over or self.game.won):
            self.running = not self.running
            self._schedule_logic_tick()
            return

        if event.keysym == "Escape":
            self._close()

    def _show_window(self) -> None:
        window_width = self.game.width * self.CELL_SIZE + 40
        window_height = self.game.height * self.CELL_SIZE + 160
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

    def _close(self) -> None:
        if self.logic_job is not None:
            self.root.after_cancel(self.logic_job)
            self.logic_job = None
        if self.render_job is not None:
            self.root.after_cancel(self.render_job)
            self.render_job = None
        self.root.destroy()

    def _reset_game(self) -> None:
        self.game.reset()
        self.running = False
        self.started = False
        self.level_banner_frames = 0
        self.food_flash_frames = 0
        self.particles.clear()
        if self.logic_job is not None:
            self.root.after_cancel(self.logic_job)
            self.logic_job = None

    def _schedule_logic_tick(self) -> None:
        if self.logic_job is not None:
            return
        if not self.started or not self.running:
            return
        if self.game.game_over or self.game.won:
            return
        self.logic_job = self.root.after(self.game.speed_ms, self._game_loop)

    def _game_loop(self) -> None:
        self.logic_job = None
        if not self.started or not self.running:
            return
        if self.game.game_over or self.game.won:
            return

        result = self.game.tick()
        self._handle_tick_result(result)

        if self.running and not (self.game.game_over or self.game.won):
            self._schedule_logic_tick()

    def _handle_tick_result(self, result: TickResult) -> None:
        if result.ate_food and result.consumed_food_position is not None:
            self.food_flash_frames = 9
            self._spawn_particles(result.consumed_food_position)
            self._persist_best_score()

        if result.level_up:
            self.level_banner_frames = 45

        if result.game_over or result.won:
            self.running = False
            self._persist_best_score()

    def _schedule_render(self) -> None:
        self.render_job = self.root.after(self.FRAME_DELAY_MS, self._render_frame)

    def _render_frame(self) -> None:
        self.render_job = None
        self.animation_frame += 1
        if self.level_banner_frames > 0:
            self.level_banner_frames -= 1
        if self.food_flash_frames > 0:
            self.food_flash_frames -= 1
        self._advance_particles()
        self._draw()
        self._schedule_render()

    def _draw(self) -> None:
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_particles()
        self._draw_food()
        self._draw_snake()
        self._draw_level_banner()
        self._draw_overlay()
        self._update_hud()

    def _draw_grid(self) -> None:
        pulse = 0.1 * math.sin(self.animation_frame / 12)
        for x in range(self.game.width):
            for y in range(self.game.height):
                base = self.GRID_LIGHT_COLOR if (x + y) % 2 == 0 else self.GRID_DARK_COLOR
                factor = max(0.0, min(1.0, 0.12 + pulse))
                color = self._blend_color(base, self.PANEL_ALT_COLOR, factor)
                self._draw_cell(
                    x,
                    y,
                    color,
                    inset=0,
                    outline="#0c2a2f",
                    outline_width=1,
                )

    def _draw_food(self) -> None:
        if self.game.food is None:
            return

        food_x, food_y = self.game.food
        pulse = (math.sin(self.animation_frame / 3) + 1) / 2
        inset = 6 - int(pulse * 2)
        self._draw_cell(
            food_x,
            food_y,
            self.FOOD_COLOR,
            inset=inset,
            outline="#7c2d12",
            outline_width=2,
        )
        self._draw_cell(
            food_x,
            food_y,
            self.FOOD_CORE_COLOR,
            inset=inset + 5,
            outline="",
            outline_width=0,
        )

        if self.food_flash_frames > 0:
            center_x, center_y = self._cell_center(food_x, food_y)
            radius = 8 + (9 - self.food_flash_frames) * 4
            self.canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                outline="#ffd166",
                width=2,
            )

    def _draw_snake(self) -> None:
        for index, (x, y) in enumerate(self.game.snake):
            if index == 0:
                color = self.SNAKE_HEAD_COLOR
                outline = "#d9ffcc"
                inset = 2
            else:
                blend = min(index / max(len(self.game.snake) - 1, 1), 1.0)
                color = self._blend_color(
                    self.SNAKE_BODY_START,
                    self.SNAKE_BODY_END,
                    blend,
                )
                outline = "#12553f"
                inset = 3

            self._draw_cell(x, y, color, inset=inset, outline=outline, outline_width=2)

            if index == 0:
                self._draw_head_details(x, y)

    def _draw_head_details(self, x: int, y: int) -> None:
        center_x, center_y = self._cell_center(x, y)
        eye_offset = 4
        eye_gap = 5
        if self.game.direction == UP:
            eye_positions = [(-eye_gap, -eye_offset), (eye_gap, -eye_offset)]
        elif self.game.direction == DOWN:
            eye_positions = [(-eye_gap, eye_offset), (eye_gap, eye_offset)]
        elif self.game.direction == LEFT:
            eye_positions = [(-eye_offset, -eye_gap), (-eye_offset, eye_gap)]
        else:
            eye_positions = [(eye_offset, -eye_gap), (eye_offset, eye_gap)]

        for dx, dy in eye_positions:
            self.canvas.create_oval(
                center_x + dx - 2,
                center_y + dy - 2,
                center_x + dx + 2,
                center_y + dy + 2,
                fill="#11250f",
                outline="",
            )

    def _draw_particles(self) -> None:
        for particle in self.particles:
            radius = max(1.5, particle["life"] * 4)
            self.canvas.create_oval(
                particle["x"] - radius,
                particle["y"] - radius,
                particle["x"] + radius,
                particle["y"] + radius,
                fill=particle["color"],
                outline="",
            )

    def _draw_level_banner(self) -> None:
        if self.level_banner_frames <= 0:
            return

        alpha_factor = min(self.level_banner_frames / 45, 1.0)
        text_color = self._blend_color(self.BANNER_COLOR, self.TEXT_COLOR, 1 - alpha_factor)
        self.canvas.create_text(
            self.game.width * self.CELL_SIZE / 2,
            24,
            text=f"Level {self.game.level}",
            fill=text_color,
            font=("Helvetica", 18, "bold"),
        )

    def _draw_overlay(self) -> None:
        message = ""
        sub_message = ""
        if not self.started:
            message = "Press an arrow key to start"
            sub_message = "Space pauses, R resets, Esc exits"
        elif self.game.won:
            message = "Board Cleared"
            sub_message = "Press Enter or R for a fresh run"
        elif self.game.game_over:
            message = "Game Over"
            sub_message = "Press Enter or R to try again"
        elif not self.running:
            message = "Paused"
            sub_message = "Press Space to continue"

        if not message:
            return

        width = self.game.width * self.CELL_SIZE
        height = self.game.height * self.CELL_SIZE
        self.canvas.create_rectangle(
            18,
            height / 2 - 62,
            width - 18,
            height / 2 + 62,
            fill=self.OVERLAY_COLOR,
            outline=self.BOARD_BORDER_COLOR,
            width=2,
            stipple="gray50",
        )
        self.canvas.create_text(
            width / 2,
            height / 2 - 12,
            text=message,
            fill=self.TEXT_COLOR,
            font=("Helvetica", 22, "bold"),
        )
        self.canvas.create_text(
            width / 2,
            height / 2 + 20,
            text=sub_message,
            fill=self.MUTED_TEXT_COLOR,
            font=("Helvetica", 11),
        )

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

    def _cell_center(self, x: int, y: int) -> tuple[float, float]:
        return (
            x * self.CELL_SIZE + self.CELL_SIZE / 2,
            y * self.CELL_SIZE + self.CELL_SIZE / 2,
        )

    def _spawn_particles(self, position: tuple[int, int]) -> None:
        center_x, center_y = self._cell_center(*position)
        for index in range(10):
            angle = (math.tau / 10) * index
            speed = 1.3 + (index % 3) * 0.35
            self.particles.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "life": 1.0,
                    "color": self.FOOD_CORE_COLOR if index % 2 == 0 else self.FOOD_COLOR,
                }
            )

    def _advance_particles(self) -> None:
        next_particles: list[dict[str, float]] = []
        for particle in self.particles:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dy"] += 0.03
            particle["life"] -= 0.06
            if particle["life"] > 0:
                next_particles.append(particle)
        self.particles = next_particles

    def _persist_best_score(self) -> None:
        if self.game.score > self.best_score:
            self.best_score = self.score_storage.save_best_score(self.game.score)

    def _update_hud(self) -> None:
        self.title_var.set("Snake Arcade")
        self.stats_var.set(
            "  ".join(
                [
                    f"Score {self.game.score:04d}",
                    f"Best {self.best_score:04d}",
                    f"Level {self.game.level}",
                    f"Speed {self.game.speed_ms}ms",
                ]
            )
        )

        if not self.started:
            footer = "Guide the snake through a clean arcade run."
        elif self.game.won:
            footer = "Perfect clear. You filled the whole board."
        elif self.game.game_over:
            footer = "One more run? The speed curve gets sharper as the level climbs."
        elif not self.running:
            footer = "Paused. Resume when you're ready."
        else:
            foods_needed = self.game.config.foods_per_level - self.game.progress_to_next_level
            footer = (
                f"Eat {foods_needed} more food"
                f"{'' if foods_needed == 1 else 's'} to reach the next level."
            )
        self.footer_var.set(footer)

    def _blend_color(self, start: str, end: str, factor: float) -> str:
        factor = max(0.0, min(1.0, factor))
        start_rgb = self._hex_to_rgb(start)
        end_rgb = self._hex_to_rgb(end)
        mixed = tuple(
            int(start_value + (end_value - start_value) * factor)
            for start_value, end_value in zip(start_rgb, end_rgb)
        )
        return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"

    def _hex_to_rgb(self, value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def main() -> None:
    app = SnakeApp()
    app.run()


if __name__ == "__main__":
    main()
