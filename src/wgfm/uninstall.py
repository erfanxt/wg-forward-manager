from __future__ import annotations

import shutil
from pathlib import Path

from .constants import (
    CONFIG_FILE,
    INSTALL_BIN,
    INSTALL_DIR,
    LOG_FILE,
    MAINS_FILE,
    RECONCILE_SERVICE,
    RECONCILE_TIMER,
    ROUTES_FILE,
    RULES_FILE,
    STATE_DIR,
    WG_CONF,
)
from .logger import log
from .utils import ask_yes_no, run


def _safe_unlink(path: Path) -> None:
    try:
        if path.is_symlink() or path.exists():
            path.unlink()
    except FileNotFoundError:
        pass


def _delete_nft_table() -> None:
    result = run(['nft', 'list', 'table', 'inet', 'wg_forward'], capture=True, check=False)
    if result.returncode == 0:
        run(['nft', 'delete', 'table', 'inet', 'wg_forward'], check=False)


def uninstall(*, confirm: bool = True) -> None:
    """Remove the manager, generated state, and system integration files."""

    if confirm and not ask_yes_no('Remove WG Forward Manager from this server?', 'no'):
        log('Uninstall cancelled.')
        return

    for unit in (
        'wgfm-reconcile.timer',
        f'wg-quick@{WG_CONF.stem}',
    ):
        run(['systemctl', 'stop', unit], check=False)
        run(['systemctl', 'disable', unit], check=False)

    # The reconcile service is a helper oneshot without an [Install] section.
    run(['systemctl', 'stop', 'wgfm-reconcile.service'], check=False)

    _delete_nft_table()

    for path in (
        RECONCILE_SERVICE,
        RECONCILE_TIMER,
        WG_CONF,
        CONFIG_FILE,
        MAINS_FILE,
        ROUTES_FILE,
        RULES_FILE,
        STATE_DIR / 'keys',
        STATE_DIR,
    ):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            _safe_unlink(path)

    for path in (
        Path('/etc/sysctl.d/99-wg-forward.conf'),
        INSTALL_BIN,
        LOG_FILE,
    ):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            _safe_unlink(path)

    shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    run(['systemctl', 'daemon-reload'], check=False)
    log('WG Forward Manager removed.')
