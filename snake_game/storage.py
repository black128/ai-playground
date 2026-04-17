from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ScoreStorage:
    path: Path = Path.home() / ".snake_game" / "scores.json"

    def load_best_score(self) -> int:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except FileNotFoundError:
            return 0
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return 0

        best_score = payload.get("best_score", 0)
        return best_score if isinstance(best_score, int) and best_score >= 0 else 0

    def save_best_score(self, score: int) -> int:
        score = max(score, 0)
        current_best = self.load_best_score()
        if score <= current_best:
            return current_best

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump({"best_score": score}, file)
        return score
