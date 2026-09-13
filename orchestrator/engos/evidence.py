from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_EVIDENCE_ROOT = Path(os.environ.get("ENGOS_EVIDENCE_ROOT", "/home/engops/projects/.engos/evidence"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    return value


class EvidenceStore:
    """Persistent per-run evidence store for Engineering OS executions."""

    def __init__(self, run_id: str, root: str | Path | None = None) -> None:
        if not run_id or "/" in run_id or "\\\\" in run_id or run_id in {".", ".."}:
            raise ValueError("invalid run_id")
        self.run_id = run_id
        self.root = Path(root) if root is not None else DEFAULT_EVIDENCE_ROOT
        self.run_dir = self.root / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        if not name or Path(name).name != name:
            raise ValueError("evidence file name must be a simple file name")
        return self.run_dir / name

    def write_json(self, name: str, payload: Any) -> Path:
        target = self.path(name)
        content = json.dumps(_jsonable(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        self._atomic_write(target, content)
        return target

    def write_text(self, name: str, content: str) -> Path:
        target = self.path(name)
        self._atomic_write(target, content)
        return target

    def append_event(self, event: dict[str, Any]) -> Path:
        target = self.path("events.jsonl")
        record = {"timestamp": utc_now(), **event}
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        return target

    def write_result(self, payload: dict[str, Any]) -> Path:
        result = {"run_id": self.run_id, "recorded_at": utc_now(), **payload}
        return self.write_json("result.json", result)

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
