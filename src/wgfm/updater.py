from __future__ import annotations
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from .backup import create_backup
from .constants import INSTALL_BIN, INSTALL_DIR, REPO_NAME, REPO_OWNER

ARCHIVE_TIMEOUT = 20
API_TIMEOUT = 10
EXECUTABLE_NAMES = {"wgfm", "install.sh", "update.sh", "uninstall.sh"}


def latest_release() -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "wg-forward-manager"})
    with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
        release = json.loads(resp.read().decode("utf-8"))
    if not isinstance(release, dict) or not release.get("tag_name"):
        raise RuntimeError("Could not read latest GitHub release.")
    return release


def _copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        target = dst / child.name
        if child.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target, copy_function=shutil.copy2)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _is_safe_path(base: Path, target: Path) -> bool:
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    try:
        return target_resolved.is_relative_to(base_resolved)
    except AttributeError:  # pragma: no cover - Python < 3.9 fallback
        return str(target_resolved).startswith(str(base_resolved).rstrip("/") + "/")


def _safe_extract_tar(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = dest / member.name
            if not _is_safe_path(dest, member_path):
                raise RuntimeError(f"Unsafe path in archive: {member.name}")
        tar.extractall(path=dest)


def _download_release_archive(url: str, destination: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "wg-forward-manager"})
    with urllib.request.urlopen(req, timeout=ARCHIVE_TIMEOUT) as resp:
        destination.write_bytes(resp.read())


def _find_release_root(extract_dir: Path) -> Path:
    roots = [p for p in extract_dir.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError("Unexpected release archive structure.")
    return roots[0]


def _mark_executables(root: Path) -> None:
    for rel in EXECUTABLE_NAMES:
        target = root / rel
        if target.exists() and target.is_file():
            mode = target.stat().st_mode
            target.chmod(mode | 0o111)


def _ensure_bin_link() -> None:
    INSTALL_BIN.parent.mkdir(parents=True, exist_ok=True)
    if INSTALL_BIN.exists() or INSTALL_BIN.is_symlink():
        INSTALL_BIN.unlink()
    INSTALL_BIN.symlink_to(INSTALL_DIR / "wgfm")


def _snapshot_install_tree() -> Path | None:
    if not INSTALL_DIR.exists():
        return None
    backup_root = Path(tempfile.mkdtemp(prefix="wgfm-code-backup-"))
    backup_tree = backup_root / INSTALL_DIR.name
    _copy_tree(INSTALL_DIR, backup_tree)
    return backup_tree


def _restore_install_tree(backup_tree: Path | None) -> None:
    if backup_tree is None or not backup_tree.exists():
        return
    if INSTALL_DIR.exists() or INSTALL_DIR.is_symlink():
        if INSTALL_DIR.is_symlink() or INSTALL_DIR.is_file():
            INSTALL_DIR.unlink()
        else:
            shutil.rmtree(INSTALL_DIR)
    _copy_tree(backup_tree, INSTALL_DIR)
    _mark_executables(INSTALL_DIR)
    _ensure_bin_link()


def _restore_archive_to_root(archive: str) -> None:
    archive_path = Path(archive)
    root = Path("/")
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            target = (root / member.name).resolve()
            if not _is_safe_path(root, target):
                raise RuntimeError(f"Unsafe path in archive: {member.name}")
        tar.extractall(path="/")


def download_and_apply() -> str:
    release = latest_release()
    tag = release["tag_name"]
    archive_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/tags/{tag}.tar.gz"

    state_backup = create_backup()
    code_backup = _snapshot_install_tree()

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tar_path = tmp / "release.tar.gz"
        extract_dir = tmp / "extract"
        stage_dir = Path(tempfile.mkdtemp(prefix="wgfm-stage-", dir=str(INSTALL_DIR.parent)))
        stage_tree = stage_dir / INSTALL_DIR.name
        try:
            _download_release_archive(archive_url, tar_path)
            _safe_extract_tar(tar_path, extract_dir)
            src_root = _find_release_root(extract_dir)
            _copy_tree(src_root, stage_tree)
            _mark_executables(stage_tree)

            if INSTALL_DIR.exists() or INSTALL_DIR.is_symlink():
                if INSTALL_DIR.is_symlink() or INSTALL_DIR.is_file():
                    INSTALL_DIR.unlink()
                else:
                    shutil.rmtree(INSTALL_DIR)

            stage_tree.replace(INSTALL_DIR)
            _mark_executables(INSTALL_DIR)
            _ensure_bin_link()
            return f"Updated to {tag} (state backup: {state_backup})"
        except Exception:
            _restore_install_tree(code_backup)
            try:
                _restore_archive_to_root(state_backup)
            except Exception:
                pass
            raise
        finally:
            shutil.rmtree(stage_dir, ignore_errors=True)
