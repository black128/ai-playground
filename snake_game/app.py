from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
from typing import Any
import webbrowser

from snake_game.engine import DIRECTIONS, GameConfig, SnakeGame, TickResult
from snake_game.storage import ScoreStorage

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Snake Arcade</title>
  <style>
    :root {
      --bg: #091218;
      --panel: rgba(12, 27, 35, 0.88);
      --panel-border: rgba(120, 200, 180, 0.28);
      --text: #ecfff9;
      --muted: #9ec2b8;
      --accent: #8ff76d;
      --warm: #ffd166;
      --danger: #ff7b6b;
      --grid-a: #10202a;
      --grid-b: #0a161d;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(143, 247, 109, 0.15), transparent 26%),
        radial-gradient(circle at top right, rgba(255, 209, 102, 0.12), transparent 24%),
        linear-gradient(180deg, #0a151c 0%, #071015 100%);
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 24px;
    }

    .shell {
      width: min(1120px, 100%);
      display: grid;
      grid-template-columns: minmax(320px, 760px) 320px;
      gap: 24px;
      align-items: start;
    }

    .stage,
    .sidebar {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 24px;
      backdrop-filter: blur(16px);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
    }

    .stage {
      padding: 24px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin-bottom: 18px;
    }

    .title-block h1 {
      margin: 0;
      font-size: clamp(28px, 4vw, 46px);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }

    .title-block p {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 15px;
    }

    .pill {
      border: 1px solid rgba(255,255,255,0.08);
      color: var(--warm);
      border-radius: 999px;
      padding: 9px 14px;
      font-size: 13px;
      background: rgba(255, 255, 255, 0.03);
    }

    .board-wrap {
      position: relative;
      aspect-ratio: 1 / 1;
      width: 100%;
      border-radius: 22px;
      overflow: hidden;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.03), transparent),
        linear-gradient(180deg, #0d1b22 0%, #091218 100%);
      border: 1px solid rgba(120, 200, 180, 0.28);
    }

    canvas {
      width: 100%;
      height: 100%;
      display: block;
    }

    .overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      pointer-events: none;
      padding: 24px;
      background: linear-gradient(180deg, rgba(4, 9, 12, 0.08), rgba(4, 9, 12, 0.5));
      opacity: 0;
      transition: opacity 180ms ease;
    }

    .overlay.visible {
      opacity: 1;
    }

    .overlay-card {
      width: min(480px, 100%);
      background: rgba(5, 12, 16, 0.82);
      border: 1px solid rgba(143, 247, 109, 0.18);
      border-radius: 22px;
      padding: 24px;
      text-align: center;
      box-shadow: 0 18px 42px rgba(0, 0, 0, 0.3);
    }

    .overlay-card h2 {
      margin: 0;
      font-size: 34px;
      letter-spacing: -0.04em;
    }

    .overlay-card p {
      margin: 10px 0 0;
      color: var(--muted);
      line-height: 1.45;
    }

    .footer {
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      color: var(--muted);
      font-size: 14px;
    }

    .sidebar {
      padding: 24px;
      display: grid;
      gap: 18px;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .metric {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .metric .label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    .metric .value {
      margin-top: 6px;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.05em;
    }

    .section h3 {
      margin: 0 0 10px;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--muted);
    }

    .status-line {
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }

    .status-help {
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.5;
    }

    .level-bar {
      margin-top: 12px;
      height: 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.06);
      overflow: hidden;
    }

    .level-bar > span {
      display: block;
      height: 100%;
      width: 0;
      background: linear-gradient(90deg, #8ff76d, #ffd166);
      transition: width 150ms linear;
    }

    .controls {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .control {
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
    }

    .control strong {
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
      color: var(--warm);
    }

    .control span {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }

    .banner {
      min-height: 52px;
      display: flex;
      align-items: center;
      border-radius: 18px;
      padding: 14px 16px;
      background: linear-gradient(90deg, rgba(143, 247, 109, 0.12), rgba(255, 209, 102, 0.08));
      border: 1px solid rgba(255, 209, 102, 0.18);
      color: var(--warm);
      font-weight: 700;
      letter-spacing: 0.02em;
      opacity: 0;
      transition: opacity 160ms ease;
    }

    .banner.visible {
      opacity: 1;
    }

    @media (max-width: 980px) {
      .shell {
        grid-template-columns: 1fr;
      }
      .sidebar {
        order: -1;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="stage">
      <div class="topbar">
        <div class="title-block">
          <h1>Snake Arcade</h1>
          <p>Python powered. Browser rendered. Reliable on this machine.</p>
        </div>
        <div class="pill" id="speed-pill">Speed 180ms</div>
      </div>
      <div class="board-wrap">
        <canvas id="board" width="720" height="720"></canvas>
        <div class="overlay visible" id="overlay">
          <div class="overlay-card">
            <h2 id="overlay-title">Press an arrow key to start</h2>
            <p id="overlay-text">The Tk window renderer is bypassed here. This is the stable full product view.</p>
          </div>
        </div>
      </div>
      <div class="footer">
        <span id="footer-left">Eat 4 foods to level up.</span>
        <span id="footer-right">Arrow keys or WASD to move</span>
      </div>
    </section>

    <aside class="sidebar">
      <div class="metric-grid">
        <div class="metric"><div class="label">Score</div><div class="value" id="score-value">0000</div></div>
        <div class="metric"><div class="label">Best</div><div class="value" id="best-value">0000</div></div>
        <div class="metric"><div class="label">Level</div><div class="value" id="level-value">1</div></div>
        <div class="metric"><div class="label">Length</div><div class="value" id="length-value">3</div></div>
      </div>

      <div class="section">
        <h3>Status</h3>
        <div class="status-line" id="status-line">Ready</div>
        <div class="status-help" id="status-help">The game polls local Python state and renders at 60fps here in the browser.</div>
        <div class="level-bar"><span id="level-progress"></span></div>
      </div>

      <div class="banner" id="banner">Level Up</div>

      <div class="section">
        <h3>Controls</h3>
        <div class="controls">
          <div class="control"><strong>Arrow / WASD</strong><span>Move and auto-start the run</span></div>
          <div class="control"><strong>Space</strong><span>Pause or resume</span></div>
          <div class="control"><strong>Enter</strong><span>Start a new round</span></div>
          <div class="control"><strong>R</strong><span>Reset instantly</span></div>
        </div>
      </div>
    </aside>
  </div>

  <script>
    const canvas = document.getElementById("board");
    const ctx = canvas.getContext("2d");
    const overlay = document.getElementById("overlay");
    const overlayTitle = document.getElementById("overlay-title");
    const overlayText = document.getElementById("overlay-text");
    const banner = document.getElementById("banner");
    const scoreValue = document.getElementById("score-value");
    const bestValue = document.getElementById("best-value");
    const levelValue = document.getElementById("level-value");
    const lengthValue = document.getElementById("length-value");
    const speedPill = document.getElementById("speed-pill");
    const statusLine = document.getElementById("status-line");
    const statusHelp = document.getElementById("status-help");
    const levelProgress = document.getElementById("level-progress");
    const footerLeft = document.getElementById("footer-left");
    const footerRight = document.getElementById("footer-right");

    const state = {
      width: 20,
      height: 20,
      snake: [],
      food: null,
      score: 0,
      best_score: 0,
      level: 1,
      speed_ms: 180,
      started: false,
      running: false,
      game_over: false,
      won: false,
      foods_per_level: 4,
      progress_to_next_level: 0,
      level_up_flash: 0,
      tick: 0
    };

    let particles = [];
    let lastFoodKey = null;

    function pad(num) {
      return String(num).padStart(4, "0");
    }

    async function postAction(action, payload = {}) {
      await fetch("/api/action", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action, ...payload})
      });
    }

    async function pollState() {
      try {
        const response = await fetch("/api/state", {cache: "no-store"});
        const next = await response.json();
        const hadFood = state.food ? `${state.food[0]}:${state.food[1]}` : null;
        const hasFood = next.food ? `${next.food[0]}:${next.food[1]}` : null;
        if (hadFood && hasFood && hadFood !== hasFood) {
          spawnParticles(state.food);
        }
        Object.assign(state, next);
        if (state.level_up_flash > 0) {
          banner.classList.add("visible");
          banner.textContent = `Level ${state.level} unlocked`;
        } else {
          banner.classList.remove("visible");
        }
        updateHud();
      } catch (error) {
        statusLine.textContent = "Connection lost";
        statusHelp.textContent = "Local Python server is not responding.";
      }
    }

    function updateHud() {
      scoreValue.textContent = pad(state.score);
      bestValue.textContent = pad(state.best_score);
      levelValue.textContent = String(state.level);
      lengthValue.textContent = String(state.snake.length || 0);
      speedPill.textContent = `Speed ${state.speed_ms}ms`;
      levelProgress.style.width = `${(state.progress_to_next_level / state.foods_per_level) * 100}%`;

      if (!state.started) {
        statusLine.textContent = "Ready";
        statusHelp.textContent = "Press an arrow key or WASD to start.";
        footerLeft.textContent = `Eat ${state.foods_per_level} foods to level up.`;
        showOverlay("Press an arrow key to start", "Space pauses, Enter starts a fresh run, R resets.");
      } else if (state.won) {
        statusLine.textContent = "Board cleared";
        statusHelp.textContent = "You filled the whole board. Enter or R starts again.";
        footerLeft.textContent = "Perfect clear achieved.";
        showOverlay("Board cleared", "Every cell is yours now. Press Enter or R for another run.");
      } else if (state.game_over) {
        statusLine.textContent = "Game over";
        statusHelp.textContent = "One more run? Enter or R restarts instantly.";
        footerLeft.textContent = "The speed curve keeps ramping each level.";
        showOverlay("Game over", "You crashed. Press Enter or R to restart.");
      } else if (!state.running) {
        statusLine.textContent = "Paused";
        statusHelp.textContent = "Press Space to continue the run.";
        footerLeft.textContent = "Take a breath and jump back in.";
        showOverlay("Paused", "Press Space to continue.");
      } else {
        const remaining = state.foods_per_level - state.progress_to_next_level;
        statusLine.textContent = "Running";
        statusHelp.textContent = `${remaining} more food${remaining === 1 ? "" : "s"} to level ${state.level + 1}.`;
        footerLeft.textContent = `${remaining} more food${remaining === 1 ? "" : "s"} to level up.`;
        hideOverlay();
      }
      footerRight.textContent = "Arrow keys / WASD move, Space pauses, R resets";
    }

    function showOverlay(title, text) {
      overlay.classList.add("visible");
      overlayTitle.textContent = title;
      overlayText.textContent = text;
    }

    function hideOverlay() {
      overlay.classList.remove("visible");
    }

    function spawnParticles(position) {
      if (!position) return;
      for (let i = 0; i < 14; i += 1) {
        const angle = (Math.PI * 2 * i) / 14;
        particles.push({
          x: position[0] + 0.5,
          y: position[1] + 0.5,
          dx: Math.cos(angle) * (0.035 + (i % 3) * 0.012),
          dy: Math.sin(angle) * (0.035 + (i % 4) * 0.01),
          life: 1,
          color: i % 2 === 0 ? "#ffd166" : "#ff7b6b"
        });
      }
    }

    function updateParticles() {
      particles = particles.filter((particle) => particle.life > 0).map((particle) => ({
        ...particle,
        x: particle.x + particle.dx,
        y: particle.y + particle.dy,
        dy: particle.dy + 0.0008,
        life: particle.life - 0.025
      }));
    }

    function blend(a, b, factor) {
      const pa = parseInt(a.slice(1), 16);
      const pb = parseInt(b.slice(1), 16);
      const ra = (pa >> 16) & 255, ga = (pa >> 8) & 255, ba = pa & 255;
      const rb = (pb >> 16) & 255, gb = (pb >> 8) & 255, bb = pb & 255;
      const r = Math.round(ra + (rb - ra) * factor);
      const g = Math.round(ga + (gb - ga) * factor);
      const b2 = Math.round(ba + (bb - ba) * factor);
      return `rgb(${r}, ${g}, ${b2})`;
    }

    function drawBoard(timestamp) {
      const size = Math.min(canvas.clientWidth, canvas.clientHeight);
      if (canvas.width !== size || canvas.height !== size) {
        canvas.width = size;
        canvas.height = size;
      }

      const cell = size / state.width;
      ctx.clearRect(0, 0, size, size);

      for (let y = 0; y < state.height; y += 1) {
        for (let x = 0; x < state.width; x += 1) {
          ctx.fillStyle = (x + y) % 2 === 0 ? "#10202a" : "#0a161d";
          ctx.fillRect(x * cell, y * cell, cell, cell);
          ctx.strokeStyle = "rgba(255,255,255,0.03)";
          ctx.strokeRect(x * cell, y * cell, cell, cell);
        }
      }

      if (state.food) {
        const pulse = 0.72 + ((Math.sin(timestamp / 180) + 1) / 2) * 0.22;
        const cx = (state.food[0] + 0.5) * cell;
        const cy = (state.food[1] + 0.5) * cell;
        ctx.beginPath();
        ctx.fillStyle = "rgba(255, 123, 107, 0.18)";
        ctx.arc(cx, cy, cell * pulse * 0.48, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.fillStyle = "#ff7b6b";
        ctx.arc(cx, cy, cell * pulse * 0.28, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.fillStyle = "#ffe4a8";
        ctx.arc(cx + cell * 0.08, cy - cell * 0.08, cell * 0.09, 0, Math.PI * 2);
        ctx.fill();
      }

      state.snake.forEach((segment, index) => {
        const x = segment[0] * cell;
        const y = segment[1] * cell;
        const inset = index === 0 ? cell * 0.1 : cell * 0.14;
        ctx.fillStyle = index === 0 ? "#8ff76d" : blend("#3dcf75", "#176f56", index / Math.max(state.snake.length - 1, 1));
        ctx.strokeStyle = index === 0 ? "#d9ffcc" : "#12553f";
        ctx.lineWidth = 2;
        roundRect(ctx, x + inset, y + inset, cell - inset * 2, cell - inset * 2, Math.max(6, cell * 0.22));
        ctx.fill();
        ctx.stroke();

        if (index === 0) {
          drawEyes(segment, cell);
        }
      });

      updateParticles();
      particles.forEach((particle) => {
        ctx.beginPath();
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = Math.max(0, particle.life);
        ctx.arc(particle.x * cell, particle.y * cell, cell * 0.08 * Math.max(0.6, particle.life), 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      });

      requestAnimationFrame(drawBoard);
    }

    function drawEyes(segment, cell) {
      let eyes;
      switch (state.direction) {
        case "Up":
          eyes = [[-0.14, -0.12], [0.14, -0.12]];
          break;
        case "Down":
          eyes = [[-0.14, 0.12], [0.14, 0.12]];
          break;
        case "Left":
          eyes = [[-0.12, -0.14], [-0.12, 0.14]];
          break;
        default:
          eyes = [[0.12, -0.14], [0.12, 0.14]];
      }
      eyes.forEach(([dx, dy]) => {
        ctx.beginPath();
        ctx.fillStyle = "#0b150d";
        ctx.arc((segment[0] + 0.5 + dx) * cell, (segment[1] + 0.5 + dy) * cell, cell * 0.05, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    function roundRect(ctx, x, y, width, height, radius) {
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.arcTo(x + width, y, x + width, y + height, radius);
      ctx.arcTo(x + width, y + height, x, y + height, radius);
      ctx.arcTo(x, y + height, x, y, radius);
      ctx.arcTo(x, y, x + width, y, radius);
      ctx.closePath();
    }

    document.addEventListener("keydown", async (event) => {
      const key = event.key;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " ", "Enter", "r", "R", "w", "W", "a", "A", "s", "S", "d", "D"].includes(key)) {
        event.preventDefault();
      }
      if (key === " ") {
        await postAction("pause");
      } else if (key === "Enter") {
        await postAction("start");
      } else if (key === "r" || key === "R") {
        await postAction("reset");
      } else if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "W", "a", "A", "s", "S", "d", "D"].includes(key)) {
        await postAction("direction", {key});
      }
      pollState();
    });

    setInterval(pollState, 80);
    pollState();
    requestAnimationFrame(drawBoard);
  </script>
</body>
</html>
"""


class BrowserSnakeController:
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
        self.started = False
        self.running = False
        self.next_tick_at = time.monotonic()
        self.level_up_flash = 0
        self.tick_counter = 0
        self.last_direction_name = "Right"
        self._lock = threading.Lock()

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            self._advance_locked()
            return self._state_locked()

    def handle_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if action == "start":
                self._reset_locked()
                self.started = True
                self.running = True
                self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
            elif action == "pause":
                if self.started and not (self.game.game_over or self.game.won):
                    self.running = not self.running
                    if self.running:
                        self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
            elif action == "reset":
                self._reset_locked()
            elif action == "direction":
                key = str(payload.get("key", ""))
                direction_name = self.KEY_ALIASES.get(key, key.removeprefix("Arrow"))
                if direction_name in DIRECTIONS:
                    if not self.started:
                        self.started = True
                        self.running = True
                    self.game.change_direction_by_key(direction_name)
                    self.last_direction_name = direction_name
                    self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)

            self._advance_locked()
            return self._state_locked()

    def _advance_locked(self) -> None:
        now = time.monotonic()
        if self.level_up_flash > 0:
            self.level_up_flash -= 1

        while (
            self.started
            and self.running
            and not (self.game.game_over or self.game.won)
            and now >= self.next_tick_at
        ):
            result = self.game.tick()
            self.tick_counter += 1
            self._handle_tick_locked(result)
            self.next_tick_at += self.game.speed_ms / 1000

    def _handle_tick_locked(self, result: TickResult) -> None:
        if result.ate_food:
            self._persist_best_locked()
        if result.level_up:
            self.level_up_flash = 18
        if result.game_over or result.won:
            self.running = False
            self._persist_best_locked()

    def _reset_locked(self) -> None:
        self.game.reset()
        self.started = False
        self.running = False
        self.level_up_flash = 0
        self.next_tick_at = time.monotonic()
        self.tick_counter = 0
        self.last_direction_name = "Right"

    def _persist_best_locked(self) -> None:
        if self.game.score > self.best_score:
            self.best_score = self.score_storage.save_best_score(self.game.score)

    def _state_locked(self) -> dict[str, Any]:
        return {
            "width": self.game.width,
            "height": self.game.height,
            "snake": self.game.snake,
            "food": self.game.food,
            "score": self.game.score,
            "best_score": self.best_score,
            "level": self.game.level,
            "speed_ms": self.game.speed_ms,
            "started": self.started,
            "running": self.running,
            "game_over": self.game.game_over,
            "won": self.game.won,
            "foods_per_level": self.game.config.foods_per_level,
            "progress_to_next_level": self.game.progress_to_next_level,
            "level_up_flash": self.level_up_flash,
            "tick": self.tick_counter,
            "direction": self.last_direction_name,
        }


def make_handler(controller: BrowserSnakeController) -> type[BaseHTTPRequestHandler]:
    class SnakeHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_html(self, content: str) -> None:
            data = content.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path in ("/", "/index.html"):
                self._send_html(HTML_PAGE)
                return
            if self.path == "/api/state":
                self._send_json(controller.get_state())
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/action":
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST)
                return

            action = str(payload.get("action", ""))
            state = controller.handle_action(action, payload)
            self._send_json(state)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return SnakeHandler


def main() -> None:
    controller = BrowserSnakeController()
    handler = make_handler(controller)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}"
    print(f"Snake Arcade browser UI running at {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
