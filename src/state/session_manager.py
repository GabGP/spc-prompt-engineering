"""Multi-turn session persistence manager with backup and audit reconstruction."""

import json
from pathlib import Path
from typing import Any


class SessionManager:
    """Manages serialization, mirrored backup, and restoration of conversation history."""

    def __init__(
        self,
        cache_path: Path | str = Path(".cache/session_cache.json"),
        backup_path: Path | str | None = None,
        logs_dir: Path | str | None = None,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.backup_path = (
            Path(backup_path) if backup_path else self.cache_path.with_suffix(".bak")
        )
        self.logs_dir = Path(logs_dir) if logs_dir is not None else None

    def _read_file_as_list(self, path: Path) -> list[dict[str, Any]] | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else None
        except (json.JSONDecodeError, OSError):
            return None

    def load_history(self, factor_x1: int) -> list[dict[str, Any]]:
        """Load history if factor_x1==0; recover from backup or audit logs if lost."""
        if factor_x1 == 1:
            return []

        data = self._read_file_as_list(self.cache_path)
        if data is not None:
            return data

        backup_data = self._read_file_as_list(self.backup_path)
        if backup_data is not None:
            self.save_history(backup_data, factor_x1=0)
            return backup_data

        if self.logs_dir and self.logs_dir.exists():
            rebuilt = self.rebuild_from_audit_logs(self.logs_dir, phase="Phase_I")
            if rebuilt:
                return rebuilt

        return []

    def save_history(self, history: list[Any], factor_x1: int) -> None:
        """Persist session history and mirror to backup if accumulating (factor_x1=0)."""
        if factor_x1 == 1:
            self.clear_cache(clear_backup=False)
            return

        serialized: list[dict[str, Any]] = []
        for item in history:
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump())
            elif isinstance(item, dict):
                serialized.append(item)
            else:
                serialized.append({"content": str(item)})

        content = json.dumps(serialized, indent=2)
        for target in (self.cache_path, self.backup_path):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            except OSError:
                pass

    def clear_cache(self, clear_backup: bool = False) -> None:
        """Remove primary session cache. Preserves backup file unless clear_backup=True."""
        targets = (
            (self.cache_path, self.backup_path)
            if clear_backup
            else (self.cache_path,)
        )
        for target in targets:
            if target.exists():
                try:
                    target.unlink()
                except OSError:
                    pass

    def get_history_turn_count(self, factor_x1: int = 0) -> int:
        """Return the number of turns currently stored."""
        return len(self.load_history(factor_x1=factor_x1))

    def rebuild_from_audit_logs(
        self, logs_dir: Path | str, phase: str = "Phase_I"
    ) -> list[dict[str, Any]]:
        """Reconstruct multi-turn history from forensic audit logs if cache is lost."""
        dir_path = Path(logs_dir)
        if not dir_path.exists():
            return []

        entries: list[tuple[int, dict[str, Any]]] = []
        for file in dir_path.glob("run_*_audit.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("phase") == phase:
                    run_id = int(data.get("run_id", 0))
                    entries.append((run_id, data))
            except (json.JSONDecodeError, OSError, ValueError):
                continue

        entries.sort(key=lambda x: x[0])
        history: list[dict[str, Any]] = []
        for _, audit in entries:
            prompt = audit.get("request_prompt") or f"Input: {audit.get('input_file', '')}"
            output = audit.get("final_output_markdown", "")
            history.append({"role": "user", "parts": [{"text": prompt}]})
            history.append({"role": "model", "parts": [{"text": output}]})

        if history:
            self.save_history(history, factor_x1=0)

        return history
