"""Multi-turn session persistence manager for Phase I context accumulation."""

import json
from pathlib import Path
from typing import Any


class SessionManager:
    """Manages serialization and restoration of conversational history."""

    def __init__(self, cache_path: Path | str = Path(".session_cache.json")) -> None:
        self.cache_path = Path(cache_path)

    def load_history(self, factor_x1: int) -> list[dict[str, Any]]:
        """Load session history if factor_x1 == 0; return empty list if resetting."""
        if factor_x1 == 1:
            return []

        if not self.cache_path.exists():
            return []

        try:
            content = self.cache_path.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, OSError):
            return []

    def save_history(self, history: list[Any], factor_x1: int) -> None:
        """Persist session history if accumulating (factor_x1=0); clear if resetting."""
        if factor_x1 == 1:
            self.clear_cache()
            return

        serialized: list[dict[str, Any]] = []
        for item in history:
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump())
            elif isinstance(item, dict):
                serialized.append(item)
            else:
                serialized.append({"content": str(item)})

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    def clear_cache(self) -> None:
        """Remove the session cache file if it exists."""
        if self.cache_path.exists():
            try:
                self.cache_path.unlink()
            except OSError:
                pass

    def get_history_turn_count(self) -> int:
        """Return the number of turns stored in the session cache."""
        history = self.load_history(factor_x1=0)
        return len(history)
