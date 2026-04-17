from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from typing import Any
import webbrowser

from snake_game.engine import DIRECTIONS, GameConfig, SnakeGame, TickResult
from snake_game.storage import LeaderboardEntry, ScoreStorage


@dataclass(frozen=True)
class DifficultyProfile:
    slug: str
    name: str
    description: str
    tagline: str
    config: GameConfig


DIFFICULTIES: dict[str, DifficultyProfile] = {
    "rookie": DifficultyProfile(
        slug="rookie",
        name="Rookie",
        description="A forgiving onboarding run with gentler speed ramps.",
        tagline="Calm warm-up",
        config=GameConfig(
            width=20,
            height=20,
            initial_length=3,
            points_per_food=10,
            foods_per_level=5,
            base_speed_ms=210,
            speed_step_ms=10,
            min_speed_ms=100,
        ),
    ),
    "arcade": DifficultyProfile(
        slug="arcade",
        name="Arcade",
        description="Balanced default mode with steady pressure and readable escalation.",
        tagline="Signature mode",
        config=GameConfig(
            width=20,
            height=20,
            initial_length=3,
            points_per_food=10,
            foods_per_level=4,
            base_speed_ms=180,
            speed_step_ms=12,
            min_speed_ms=72,
        ),
    ),
    "expert": DifficultyProfile(
        slug="expert",
        name="Expert",
        description="Aggressive tempo and faster level climbs for confident players.",
        tagline="No mercy",
        config=GameConfig(
            width=20,
            height=20,
            initial_length=4,
            points_per_food=12,
            foods_per_level=3,
            base_speed_ms=150,
            speed_step_ms=15,
            min_speed_ms=58,
        ),
    ),
}


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Snake Arcade</title>
  <style>
    :root {
      --bg: #081117;
      --panel: rgba(8, 22, 30, 0.84);
      --panel-border: rgba(122, 212, 186, 0.18);
      --text: #ecfff8;
      --muted: #99b6af;
      --accent: #8ff76d;
      --warm: #ffd166;
      --danger: #ff7b6b;
      --surface: rgba(255,255,255,0.04);
      --surface-strong: rgba(255,255,255,0.08);
      --card-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
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
        radial-gradient(circle at top left, rgba(143, 247, 109, 0.14), transparent 26%),
        radial-gradient(circle at top right, rgba(255, 209, 102, 0.12), transparent 24%),
        linear-gradient(180deg, #0b161d 0%, #071015 100%);
      padding: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .shell {
      width: min(1240px, 100%);
      display: grid;
      grid-template-columns: minmax(320px, 780px) 380px;
      gap: 24px;
      align-items: start;
    }

    .stage,
    .sidebar {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 28px;
      backdrop-filter: blur(18px);
      box-shadow: var(--card-shadow);
    }

    .stage { padding: 24px; }
    .sidebar { padding: 24px; display: grid; gap: 18px; }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin-bottom: 18px;
    }

    .title-block h1 {
      margin: 0;
      font-size: clamp(32px, 4vw, 52px);
      line-height: 0.92;
      letter-spacing: -0.06em;
    }

    .title-block p {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 15px;
    }

    .pill-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
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
      border-radius: 24px;
      overflow: hidden;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.03), transparent),
        linear-gradient(180deg, #0d1b22 0%, #091218 100%);
      border: 1px solid rgba(120, 200, 180, 0.24);
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
      padding: 24px;
      background: linear-gradient(180deg, rgba(3, 8, 11, 0.06), rgba(3, 8, 11, 0.58));
      opacity: 0;
      pointer-events: none;
      transition: opacity 180ms ease;
    }

    .overlay.visible {
      opacity: 1;
      pointer-events: auto;
    }

    .overlay-card {
      width: min(560px, 100%);
      background: rgba(4, 11, 15, 0.86);
      border: 1px solid rgba(143, 247, 109, 0.12);
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 24px 54px rgba(0, 0, 0, 0.34);
    }

    .overlay-card h2 {
      margin: 0;
      font-size: 34px;
      line-height: 0.95;
      letter-spacing: -0.05em;
    }

    .overlay-card p {
      margin: 10px 0 0;
      color: var(--muted);
      line-height: 1.5;
    }

    .menu-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }

    .button {
      appearance: none;
      border: none;
      border-radius: 16px;
      padding: 13px 18px;
      font: inherit;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease, border-color 120ms ease;
    }

    .button:hover { transform: translateY(-1px); }
    .button:active { transform: translateY(0); }

    .button.primary {
      background: linear-gradient(135deg, #8ff76d, #5fd49c);
      color: #07110c;
      font-weight: 700;
    }

    .button.secondary {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      color: var(--text);
    }

    .difficulty-grid {
      display: grid;
      gap: 12px;
      margin-top: 18px;
    }

    .difficulty-card {
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 18px;
      padding: 16px;
      cursor: pointer;
      transition: border-color 140ms ease, background 140ms ease, transform 140ms ease;
    }

    .difficulty-card:hover {
      transform: translateY(-1px);
      background: rgba(255,255,255,0.045);
    }

    .difficulty-card.active {
      border-color: rgba(143, 247, 109, 0.52);
      background: linear-gradient(135deg, rgba(143,247,109,0.12), rgba(255,209,102,0.06));
    }

    .difficulty-top {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
    }

    .difficulty-name {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }

    .difficulty-tag {
      color: var(--warm);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
    }

    .difficulty-copy {
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.5;
      font-size: 14px;
    }

    .footer {
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      color: var(--muted);
      font-size: 14px;
    }

    .section h3 {
      margin: 0 0 12px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--muted);
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .metric {
      padding: 16px;
      border-radius: 18px;
      background: var(--surface);
      border: 1px solid rgba(255,255,255,0.06);
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

    .status-card,
    .leaderboard,
    .utility-bar {
      padding: 18px;
      border-radius: 20px;
      background: var(--surface);
      border: 1px solid rgba(255,255,255,0.06);
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

    .utility-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .utility-bar .button {
      flex: 1 1 120px;
      min-width: 120px;
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

    .leaderboard-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 12px;
    }

    .leaderboard-title {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }

    .leaderboard-subtitle {
      color: var(--muted);
      font-size: 13px;
    }

    .leaderboard-list {
      display: grid;
      gap: 8px;
    }

    .leaderboard-empty {
      color: var(--muted);
      font-size: 14px;
      padding: 8px 0 4px;
    }

    .leaderboard-item {
      display: grid;
      grid-template-columns: 34px 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.05);
    }

    .leaderboard-rank {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,0.06);
      font-weight: 700;
      color: var(--warm);
    }

    .leaderboard-main {
      display: grid;
      gap: 4px;
    }

    .leaderboard-score {
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .leaderboard-meta {
      color: var(--muted);
      font-size: 12px;
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

    .banner.visible { opacity: 1; }

    @media (max-width: 1020px) {
      .shell { grid-template-columns: 1fr; }
      .sidebar { order: -1; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="stage">
      <div class="topbar">
        <div class="title-block">
          <h1>Snake Arcade</h1>
          <p>Local Python backend. Browser-rendered product shell with sound, menus, and leaderboard.</p>
        </div>
        <div class="pill-row">
          <div class="pill" id="difficulty-pill">Arcade</div>
          <div class="pill" id="speed-pill">Speed 180ms</div>
        </div>
      </div>

      <div class="board-wrap">
        <canvas id="board" width="720" height="720"></canvas>
        <div class="overlay visible" id="overlay">
          <div class="overlay-card">
            <h2 id="overlay-title">Choose a mode and launch</h2>
            <p id="overlay-text">This stable browser edition replaces the blank Tk window renderer on your machine.</p>
            <div class="difficulty-grid" id="difficulty-grid"></div>
            <div class="menu-actions">
              <button class="button primary" id="start-button">Start Run</button>
              <button class="button secondary" id="menu-reset-button">Reset Board</button>
            </div>
          </div>
        </div>
      </div>

      <div class="footer">
        <span id="footer-left">Pick a difficulty and start the run.</span>
        <span id="footer-right">Arrow keys / WASD move, Space pauses</span>
      </div>
    </section>

    <aside class="sidebar">
      <div class="metric-grid">
        <div class="metric"><div class="label">Score</div><div class="value" id="score-value">0000</div></div>
        <div class="metric"><div class="label">Best</div><div class="value" id="best-value">0000</div></div>
        <div class="metric"><div class="label">Level</div><div class="value" id="level-value">1</div></div>
        <div class="metric"><div class="label">Length</div><div class="value" id="length-value">3</div></div>
      </div>

      <div class="status-card section">
        <h3>Status</h3>
        <div class="status-line" id="status-line">Ready</div>
        <div class="status-help" id="status-help">Select a difficulty, then press Start Run or use an arrow key to jump in.</div>
        <div class="level-bar"><span id="level-progress"></span></div>
      </div>

      <div class="utility-bar">
        <button class="button primary" id="sidebar-start">Start Run</button>
        <button class="button secondary" id="pause-button">Pause</button>
        <button class="button secondary" id="reset-button">Reset</button>
        <button class="button secondary" id="sound-button">Sound On</button>
      </div>

      <div class="banner" id="banner">Level Up</div>

      <div class="leaderboard section">
        <div class="leaderboard-head">
          <div>
            <div class="leaderboard-title">Leaderboard</div>
            <div class="leaderboard-subtitle" id="leaderboard-subtitle">Current difficulty standings</div>
          </div>
          <div class="pill" id="leaderboard-pill">Top 5</div>
        </div>
        <div class="leaderboard-list" id="leaderboard-list"></div>
      </div>

      <div class="section">
        <h3>Controls</h3>
        <div class="controls">
          <div class="control"><strong>Arrow / WASD</strong><span>Move and auto-start the run</span></div>
          <div class="control"><strong>Space</strong><span>Pause or resume</span></div>
          <div class="control"><strong>Enter</strong><span>Start a fresh round</span></div>
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
    const difficultyGrid = document.getElementById("difficulty-grid");
    const startButton = document.getElementById("start-button");
    const menuResetButton = document.getElementById("menu-reset-button");
    const sidebarStart = document.getElementById("sidebar-start");
    const pauseButton = document.getElementById("pause-button");
    const resetButton = document.getElementById("reset-button");
    const soundButton = document.getElementById("sound-button");
    const banner = document.getElementById("banner");
    const scoreValue = document.getElementById("score-value");
    const bestValue = document.getElementById("best-value");
    const levelValue = document.getElementById("level-value");
    const lengthValue = document.getElementById("length-value");
    const difficultyPill = document.getElementById("difficulty-pill");
    const speedPill = document.getElementById("speed-pill");
    const statusLine = document.getElementById("status-line");
    const statusHelp = document.getElementById("status-help");
    const levelProgress = document.getElementById("level-progress");
    const footerLeft = document.getElementById("footer-left");
    const footerRight = document.getElementById("footer-right");
    const leaderboardList = document.getElementById("leaderboard-list");
    const leaderboardSubtitle = document.getElementById("leaderboard-subtitle");
    const leaderboardPill = document.getElementById("leaderboard-pill");

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
      selected_difficulty: "arcade",
      active_difficulty: "arcade",
      difficulty_options: [],
      leaderboard_current: [],
      event_id: 0,
      recent_events: [],
      direction: "Right",
      tick: 0
    };

    let particles = [];
    let seenEventId = 0;
    let audioContext = null;
    let soundEnabled = localStorage.getItem("snake_arcade_sound") !== "off";

    function pad(num) {
      return String(num).padStart(4, "0");
    }

    function setSoundButton() {
      soundButton.textContent = soundEnabled ? "Sound On" : "Sound Off";
    }

    function ensureAudio() {
      if (!soundEnabled) return null;
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioContext.state === "suspended") {
        audioContext.resume();
      }
      return audioContext;
    }

    function playTone({frequency, duration = 0.12, type = "sine", gain = 0.03, slideTo = null}) {
      const audio = ensureAudio();
      if (!audio) return;
      const now = audio.currentTime;
      const oscillator = audio.createOscillator();
      const envelope = audio.createGain();
      oscillator.type = type;
      oscillator.frequency.setValueAtTime(frequency, now);
      if (slideTo) {
        oscillator.frequency.exponentialRampToValueAtTime(slideTo, now + duration);
      }
      envelope.gain.setValueAtTime(0.0001, now);
      envelope.gain.exponentialRampToValueAtTime(gain, now + 0.015);
      envelope.gain.exponentialRampToValueAtTime(0.0001, now + duration);
      oscillator.connect(envelope);
      envelope.connect(audio.destination);
      oscillator.start(now);
      oscillator.stop(now + duration + 0.02);
    }

    function playEventSound(eventName) {
      if (!soundEnabled) return;
      if (eventName === "start") {
        playTone({frequency: 440, slideTo: 660, duration: 0.13, type: "triangle", gain: 0.04});
      } else if (eventName === "eat") {
        playTone({frequency: 620, slideTo: 840, duration: 0.1, type: "square", gain: 0.03});
      } else if (eventName === "level_up") {
        playTone({frequency: 392, slideTo: 784, duration: 0.2, type: "triangle", gain: 0.045});
        setTimeout(() => playTone({frequency: 784, slideTo: 988, duration: 0.16, type: "triangle", gain: 0.035}), 70);
      } else if (eventName === "game_over") {
        playTone({frequency: 240, slideTo: 120, duration: 0.22, type: "sawtooth", gain: 0.03});
      } else if (eventName === "win") {
        playTone({frequency: 660, slideTo: 990, duration: 0.18, type: "triangle", gain: 0.04});
        setTimeout(() => playTone({frequency: 990, slideTo: 1320, duration: 0.16, type: "triangle", gain: 0.03}), 80);
      } else if (eventName === "pause") {
        playTone({frequency: 300, slideTo: 260, duration: 0.08, type: "square", gain: 0.02});
      } else if (eventName === "resume") {
        playTone({frequency: 360, slideTo: 460, duration: 0.08, type: "square", gain: 0.02});
      } else if (eventName === "difficulty_changed") {
        playTone({frequency: 520, slideTo: 600, duration: 0.07, type: "triangle", gain: 0.02});
      } else if (eventName === "reset") {
        playTone({frequency: 420, slideTo: 320, duration: 0.09, type: "triangle", gain: 0.02});
      }
    }

    async function postAction(action, payload = {}) {
      const response = await fetch("/api/action", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action, ...payload})
      });
      const next = await response.json();
      applyState(next);
    }

    async function pollState() {
      try {
        const response = await fetch("/api/state", {cache: "no-store"});
        const next = await response.json();
        applyState(next);
      } catch (error) {
        statusLine.textContent = "Connection lost";
        statusHelp.textContent = "Local Python server is not responding.";
      }
    }

    function applyState(next) {
      const previousFood = state.food ? `${state.food[0]}:${state.food[1]}` : null;
      const nextFood = next.food ? `${next.food[0]}:${next.food[1]}` : null;
      if (previousFood && nextFood && previousFood !== nextFood) {
        spawnParticles(state.food);
      }
      Object.assign(state, next);
      if (state.event_id > seenEventId) {
        seenEventId = state.event_id;
        state.recent_events.forEach(playEventSound);
      }
      updateHud();
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

    function roundRect(ctx, x, y, width, height, radius) {
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.arcTo(x + width, y, x + width, y + height, radius);
      ctx.arcTo(x + width, y + height, x, y + height, radius);
      ctx.arcTo(x, y + height, x, y, radius);
      ctx.arcTo(x, y, x + width, y, radius);
      ctx.closePath();
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
        ctx.fillStyle = "#08110b";
        ctx.arc((segment[0] + 0.5 + dx) * cell, (segment[1] + 0.5 + dy) * cell, cell * 0.05, 0, Math.PI * 2);
        ctx.fill();
      });
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

    function renderDifficultyCards() {
      difficultyGrid.innerHTML = "";
      state.difficulty_options.forEach((difficulty) => {
        const card = document.createElement("button");
        card.className = `difficulty-card ${difficulty.slug === state.selected_difficulty ? "active" : ""}`;
        card.innerHTML = `
          <div class="difficulty-top">
            <div class="difficulty-name">${difficulty.name}</div>
            <div class="difficulty-tag">${difficulty.tagline}</div>
          </div>
          <div class="difficulty-copy">${difficulty.description}</div>
        `;
        card.addEventListener("click", () => postAction("set_difficulty", {difficulty: difficulty.slug}));
        difficultyGrid.appendChild(card);
      });
    }

    function renderLeaderboard() {
      leaderboardList.innerHTML = "";
      if (!state.leaderboard_current.length) {
        const empty = document.createElement("div");
        empty.className = "leaderboard-empty";
        empty.textContent = "No runs recorded yet for this difficulty.";
        leaderboardList.appendChild(empty);
        return;
      }

      state.leaderboard_current.forEach((entry, index) => {
        const item = document.createElement("div");
        item.className = "leaderboard-item";
        item.innerHTML = `
          <div class="leaderboard-rank">${index + 1}</div>
          <div class="leaderboard-main">
            <div class="leaderboard-score">${String(entry.score).padStart(4, "0")} pts</div>
            <div class="leaderboard-meta">Level ${entry.level} • ${entry.foods_eaten} foods • ${entry.steps} steps</div>
          </div>
          <div class="leaderboard-meta">${entry.achieved_at.slice(0, 10)}</div>
        `;
        leaderboardList.appendChild(item);
      });
    }

    function updateHud() {
      scoreValue.textContent = pad(state.score);
      bestValue.textContent = pad(state.best_score);
      levelValue.textContent = String(state.level);
      lengthValue.textContent = String(state.snake.length || 0);
      speedPill.textContent = `Speed ${state.speed_ms}ms`;
      const selectedDifficulty = state.difficulty_options.find((item) => item.slug === state.selected_difficulty);
      difficultyPill.textContent = selectedDifficulty ? selectedDifficulty.name : state.selected_difficulty;
      levelProgress.style.width = `${(state.progress_to_next_level / state.foods_per_level) * 100}%`;
      leaderboardSubtitle.textContent = `${difficultyPill.textContent} standings`;
      leaderboardPill.textContent = "Top 5";
      pauseButton.textContent = state.running ? "Pause" : "Resume";

      renderDifficultyCards();
      renderLeaderboard();

      if (state.level_up_flash > 0) {
        banner.classList.add("visible");
        banner.textContent = `Level ${state.level} unlocked`;
      } else {
        banner.classList.remove("visible");
      }

      if (!state.started) {
        showOverlay(
          "Choose a mode and launch",
          "This stable browser edition replaces the blank Tk window renderer on your machine."
        );
        statusLine.textContent = "Ready";
        statusHelp.textContent = "Select a difficulty, then press Start Run or use an arrow key to jump in.";
        footerLeft.textContent = "Pick a difficulty and start the run.";
      } else if (state.won) {
        showOverlay(
          "Board cleared",
          "That run is now recorded on the leaderboard. Change difficulty or start another round."
        );
        statusLine.textContent = "Victory";
        statusHelp.textContent = "Perfect clear. Press Start Run, Enter, or choose another difficulty.";
        footerLeft.textContent = "Full board clear recorded.";
      } else if (state.game_over) {
        showOverlay(
          "Game over",
          "Your score has been recorded. Press Start Run for another attempt or switch difficulty."
        );
        statusLine.textContent = "Crash detected";
        statusHelp.textContent = "Your run is stored. Reset or jump straight back in.";
        footerLeft.textContent = "The leaderboard updates after every finished run.";
      } else if (!state.running) {
        showOverlay("Paused", "Press Space or Resume to keep the run moving.");
        statusLine.textContent = "Paused";
        statusHelp.textContent = "Take a breath. Resume when you're ready.";
        footerLeft.textContent = "The run is paused in place.";
      } else {
        hideOverlay();
        const remaining = state.foods_per_level - state.progress_to_next_level;
        statusLine.textContent = "Running";
        statusHelp.textContent = `${remaining} more food${remaining === 1 ? "" : "s"} to reach level ${state.level + 1}.`;
        footerLeft.textContent = `${remaining} more food${remaining === 1 ? "" : "s"} until the next speed boost.`;
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

    document.addEventListener("keydown", async (event) => {
      const key = event.key;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " ", "Enter", "r", "R", "w", "W", "a", "A", "s", "S", "d", "D"].includes(key)) {
        event.preventDefault();
      }
      ensureAudio();
      if (key === " ") {
        await postAction("pause");
      } else if (key === "Enter") {
        await postAction("start");
      } else if (key === "r" || key === "R") {
        await postAction("reset");
      } else if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "W", "a", "A", "s", "S", "d", "D"].includes(key)) {
        await postAction("direction", {key});
      }
    });

    startButton.addEventListener("click", () => {
      ensureAudio();
      postAction("start");
    });
    sidebarStart.addEventListener("click", () => {
      ensureAudio();
      postAction("start");
    });
    pauseButton.addEventListener("click", () => {
      ensureAudio();
      postAction("pause");
    });
    resetButton.addEventListener("click", () => {
      ensureAudio();
      postAction("reset");
    });
    menuResetButton.addEventListener("click", () => {
      ensureAudio();
      postAction("reset");
    });
    soundButton.addEventListener("click", () => {
      soundEnabled = !soundEnabled;
      localStorage.setItem("snake_arcade_sound", soundEnabled ? "on" : "off");
      setSoundButton();
      if (soundEnabled) {
        playTone({frequency: 520, slideTo: 740, duration: 0.08, type: "triangle", gain: 0.02});
      }
    });

    setSoundButton();
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

    def __init__(
        self,
        *,
        storage: ScoreStorage | None = None,
        initial_difficulty: str = "arcade",
    ) -> None:
        self.score_storage = storage or ScoreStorage()
        self.best_score = self.score_storage.load_best_score()
        self.selected_difficulty = self._normalize_difficulty(initial_difficulty)
        self.active_difficulty = self.selected_difficulty
        self.game = SnakeGame(self._profile(self.selected_difficulty).config)
        self.started = False
        self.running = False
        self.next_tick_at = time.monotonic()
        self.level_up_flash = 0
        self.tick_counter = 0
        self.last_direction_name = "Right"
        self.event_id = 0
        self.last_events: list[str] = []
        self.run_recorded = False
        self._lock = threading.Lock()

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            self._advance_locked()
            return self._state_locked()

    def handle_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if action == "start":
                self._start_run_locked()
            elif action == "pause":
                self._toggle_pause_locked()
            elif action == "reset":
                self._reset_to_menu_locked()
                self._emit_events_locked("reset")
            elif action == "set_difficulty":
                difficulty = self._normalize_difficulty(str(payload.get("difficulty", self.selected_difficulty)))
                if difficulty != self.selected_difficulty:
                    self.selected_difficulty = difficulty
                    if not (self.started and self.running):
                        self._reset_to_menu_locked(emit_event=False)
                    self._emit_events_locked("difficulty_changed")
            elif action == "direction":
                key = str(payload.get("key", ""))
                direction_name = self.KEY_ALIASES.get(key, key.removeprefix("Arrow"))
                if direction_name in DIRECTIONS:
                    if not self.started or self.game.game_over or self.game.won:
                        self._start_run_locked()
                    self.game.change_direction_by_key(direction_name)
                    self.last_direction_name = direction_name
                    self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)

            self._advance_locked()
            return self._state_locked()

    def _normalize_difficulty(self, slug: str) -> str:
        return slug if slug in DIFFICULTIES else "arcade"

    def _profile(self, slug: str) -> DifficultyProfile:
        return DIFFICULTIES[self._normalize_difficulty(slug)]

    def _reset_to_menu_locked(self, emit_event: bool = False) -> None:
        profile = self._profile(self.selected_difficulty)
        self.game = SnakeGame(profile.config)
        self.active_difficulty = self.selected_difficulty
        self.started = False
        self.running = False
        self.level_up_flash = 0
        self.next_tick_at = time.monotonic()
        self.tick_counter = 0
        self.last_direction_name = "Right"
        self.run_recorded = False
        if emit_event:
            self._emit_events_locked("reset")

    def _start_run_locked(self) -> None:
        profile = self._profile(self.selected_difficulty)
        if not self.started or self.game.game_over or self.game.won or self.active_difficulty != self.selected_difficulty:
            self.game = SnakeGame(profile.config)
            self.active_difficulty = self.selected_difficulty
            self.tick_counter = 0
            self.last_direction_name = "Right"
            self.run_recorded = False
        self.started = True
        self.running = True
        self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
        self._emit_events_locked("start")

    def _toggle_pause_locked(self) -> None:
        if not self.started or self.game.game_over or self.game.won:
            return
        self.running = not self.running
        if self.running:
            self.next_tick_at = time.monotonic() + (self.game.speed_ms / 1000)
            self._emit_events_locked("resume")
        else:
            self._emit_events_locked("pause")

    def _advance_locked(self) -> None:
        if self.level_up_flash > 0:
            self.level_up_flash -= 1

        now = time.monotonic()
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
        events: list[str] = []
        if result.ate_food:
            events.append("eat")
            self._persist_best_locked()
        if result.level_up:
            self.level_up_flash = 18
            events.append("level_up")
        if result.game_over:
            self.running = False
            events.append("game_over")
            self._persist_run_locked()
        elif result.won:
            self.running = False
            events.append("win")
            self._persist_run_locked()

        if events:
            self._emit_events_locked(*events)

    def _persist_best_locked(self) -> None:
        if self.game.score > self.best_score:
            self.best_score = self.score_storage.save_best_score(self.game.score)

    def _persist_run_locked(self) -> None:
        if self.run_recorded:
            return
        self.run_recorded = True
        self.score_storage.record_run(
            score=self.game.score,
            difficulty=self.active_difficulty,
            level=self.game.level,
            foods_eaten=self.game.foods_eaten,
            steps=self.game.steps,
        )
        self._persist_best_locked()

    def _emit_events_locked(self, *events: str) -> None:
        normalized = [event for event in events if event]
        if not normalized:
            return
        self.event_id += 1
        self.last_events = normalized

    def _difficulty_state(self) -> list[dict[str, Any]]:
        return [
            {
                "slug": profile.slug,
                "name": profile.name,
                "description": profile.description,
                "tagline": profile.tagline,
            }
            for profile in DIFFICULTIES.values()
        ]

    def _serialize_entry(self, entry: LeaderboardEntry) -> dict[str, Any]:
        return {
            "score": entry.score,
            "difficulty": entry.difficulty,
            "level": entry.level,
            "foods_eaten": entry.foods_eaten,
            "steps": entry.steps,
            "achieved_at": entry.achieved_at,
        }

    def _state_locked(self) -> dict[str, Any]:
        current_board = self.game
        leaderboard_current = [
            self._serialize_entry(entry)
            for entry in self.score_storage.load_leaderboard(
                difficulty=self.selected_difficulty,
                limit=5,
            )
        ]
        return {
            "width": current_board.width,
            "height": current_board.height,
            "snake": current_board.snake,
            "food": current_board.food,
            "score": current_board.score,
            "best_score": self.best_score,
            "level": current_board.level,
            "speed_ms": current_board.speed_ms,
            "started": self.started,
            "running": self.running,
            "game_over": current_board.game_over,
            "won": current_board.won,
            "foods_per_level": current_board.config.foods_per_level,
            "progress_to_next_level": current_board.progress_to_next_level,
            "level_up_flash": self.level_up_flash,
            "selected_difficulty": self.selected_difficulty,
            "active_difficulty": self.active_difficulty,
            "difficulty_options": self._difficulty_state(),
            "leaderboard_current": leaderboard_current,
            "event_id": self.event_id,
            "recent_events": self.last_events,
            "direction": self.last_direction_name,
            "tick": self.tick_counter,
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

            state = controller.handle_action(str(payload.get("action", "")), payload)
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
    webbrowser.open(url, new=1)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
