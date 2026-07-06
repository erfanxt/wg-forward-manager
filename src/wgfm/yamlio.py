from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .errors import ConfigError
from .utils import atomic_write


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a YAML mapping in {path}")
    return data


def dump_yaml(path: Path, data: Dict[str, Any]) -> None:
    atomic_write(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True), mode=0o600)
