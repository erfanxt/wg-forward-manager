from __future__ import annotations

from .config import load_config, save_config
from .backup import create_backup, restore_backup
from .updater import download_and_apply
from .wireguard import ensure_front_keys, ensure_node_keys, apply_front, apply_main
from .nftables import apply_front as apply_front_nft
from .system import write_sysctl_forwarding, write_systemd_units, enable_services
from .health import doctor as health_doctor
from .constants import INSTALL_DIR


def reconcile(cfg: dict) -> None:
    if cfg.get("role") == "front":
        ensure_front_keys(cfg)
        apply_front(cfg)
        apply_front_nft(cfg)
    else:
        ensure_node_keys(cfg)
        apply_main(cfg)
    save_config(cfg)


def repair(cfg: dict) -> dict:
    """
    Re-apply the current installation state and restore the minimal runtime
    services that WG Forward Manager depends on.

    This is intentionally idempotent so it can be called after reboot or after
    a partial config failure.
    """
    actions: list[str] = []

    write_sysctl_forwarding()
    actions.append("sysctl")

    write_systemd_units(str(INSTALL_DIR / "wgfm"))
    actions.append("systemd")

    enable_services()
    actions.append("services")

    if cfg.get("role") == "front":
        ensure_front_keys(cfg)
        apply_front(cfg)
        apply_front_nft(cfg)
        actions.append("front")
    elif cfg.get("role") == "main":
        ensure_node_keys(cfg)
        apply_main(cfg)
        actions.append("main")

    save_config(cfg)
    return {
        "ok": True,
        "actions": actions,
        "doctor": health_doctor(),
    }


def version() -> str:
    from .constants import APP_VERSION
    return APP_VERSION


def update() -> str:
    return download_and_apply()
