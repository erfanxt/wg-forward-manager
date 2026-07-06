from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
from .constants import LOG_FILE


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_log_dir() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    line = f"[{_stamp()}] {message}"
    try:
        _ensure_log_dir()
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
    print(message)


def warn(message: str) -> None:
    log(f"WARN: {message}")


def error(message: str) -> None:
    log(f"ERROR: {message}")


def read_logs(limit: int = 200) -> list[str]:
    try:
        if not LOG_FILE.exists():
            return []
        buffer: deque[str] = deque(maxlen=max(1, limit))
        with LOG_FILE.open("r", encoding="utf-8") as fh:
            for line in fh:
                buffer.append(line.rstrip("\n"))
        return list(buffer)
    except Exception:
        return []
