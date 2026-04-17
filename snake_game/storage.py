from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LeaderboardEntry:
    score: int
    difficulty: str
    level: int
    foods_eaten: int
    steps: int
    achieved_at: str


@dataclass
class ScoreStorage:
    path: Path = Path.home() / ".snake_game" / "scores.json"
    max_entries: int = 20

    def load_best_score(self) -> int:
        payload = self._load_payload()
        best_score = payload.get("best_score", 0)
        return best_score if isinstance(best_score, int) and best_score >= 0 else 0

    def save_best_score(self, score: int) -> int:
        score = max(score, 0)
        payload = self._load_payload()
        current_best = payload.get("best_score", 0)
        if not isinstance(current_best, int) or current_best < 0:
            current_best = 0
        if score > current_best:
            payload["best_score"] = score
            self._save_payload(payload)
            return score
        return current_best

    def load_leaderboard(self, difficulty: str | None = None, limit: int = 8) -> list[LeaderboardEntry]:
        payload = self._load_payload()
        raw_entries = payload.get("leaderboard", [])
        if not isinstance(raw_entries, list):
            return []

        entries = [self._parse_entry(item) for item in raw_entries]
        entries = [entry for entry in entries if entry is not None]
        if difficulty is not None:
            entries = [entry for entry in entries if entry.difficulty == difficulty]
        return entries[: max(limit, 0)]

    def record_run(
        self,
        *,
        score: int,
        difficulty: str,
        level: int,
        foods_eaten: int,
        steps: int,
    ) -> list[LeaderboardEntry]:
        payload = self._load_payload()
        raw_entries = payload.get("leaderboard", [])
        if not isinstance(raw_entries, list):
            raw_entries = []

        entry = LeaderboardEntry(
            score=max(score, 0),
            difficulty=difficulty,
            level=max(level, 1),
            foods_eaten=max(foods_eaten, 0),
            steps=max(steps, 0),
            achieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

        entries = [self._parse_entry(item) for item in raw_entries]
        entries = [existing for existing in entries if existing is not None]
        entries.append(entry)
        entries.sort(
            key=lambda item: (
                -item.score,
                -item.level,
                -item.foods_eaten,
                item.steps,
                item.achieved_at,
            )
        )
        entries = entries[: self.max_entries]

        payload["leaderboard"] = [asdict(item) for item in entries]
        payload["best_score"] = max(payload.get("best_score", 0), entry.score)
        self._save_payload(payload)
        return entries

    def _load_payload(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except FileNotFoundError:
            return {"best_score": 0, "leaderboard": []}
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return {"best_score": 0, "leaderboard": []}

        if not isinstance(payload, dict):
            return {"best_score": 0, "leaderboard": []}

        payload.setdefault("best_score", 0)
        payload.setdefault("leaderboard", [])
        return payload

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=True, indent=2)

    def _parse_entry(self, item: Any) -> LeaderboardEntry | None:
        if not isinstance(item, dict):
            return None
        try:
            score = int(item.get("score", 0))
            level = int(item.get("level", 1))
            foods_eaten = int(item.get("foods_eaten", 0))
            steps = int(item.get("steps", 0))
            difficulty = str(item.get("difficulty", "normal"))
            achieved_at = str(item.get("achieved_at", ""))
        except (TypeError, ValueError):
            return None

        if score < 0 or level < 1 or foods_eaten < 0 or steps < 0:
            return None

        return LeaderboardEntry(
            score=score,
            difficulty=difficulty,
            level=level,
            foods_eaten=foods_eaten,
            steps=steps,
            achieved_at=achieved_at,
        )
