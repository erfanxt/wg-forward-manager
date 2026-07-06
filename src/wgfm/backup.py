from __future__ import annotations

import tarfile
from datetime import datetime
from pathlib import Path

from .constants import STATE_DIR, WG_CONF, RECONCILE_SERVICE, RECONCILE_TIMER
from .errors import ConfigError
from .logger import log


def _safe_backup_destination(destination: str | None) -> Path:
    out = Path(destination) if destination else Path("/root") / f"wgfm-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.tar.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def _is_safe_member(member: tarfile.TarInfo) -> bool:
    name = member.name
    if not name or name.startswith("/") or name.startswith("..") or "/../" in name:
        return False
    if member.issym() or member.islnk() or member.isdev():
        return False
    return True


def create_backup(destination: str | None = None) -> str:
    out = _safe_backup_destination(destination)
    log(f"Creating backup at {out}")
    with tarfile.open(out, "w:gz") as tar:
        for item in (STATE_DIR, WG_CONF, RECONCILE_SERVICE, RECONCILE_TIMER):
            if item.exists():
                tar.add(item, arcname=str(item).lstrip("/"))
    log(f"Backup created: {out}")
    return str(out)


def restore_backup(archive: str) -> None:
    log(f"Restoring backup from {archive}")
    archive_path = Path(archive)
    if not archive_path.exists():
        raise ConfigError(f"Backup archive not found: {archive}")
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            if not _is_safe_member(member):
                raise ConfigError(f"Unsafe path in backup archive: {member.name}")
        for member in members:
            tar.extract(member, path="/", set_attrs=True)
    log("Backup restored")
