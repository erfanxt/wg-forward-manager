from __future__ import annotations

from .constants import WG_CONF, CONFIG_FILE, MAINS_FILE, ROUTES_FILE, STATE_DIR, RULES_FILE
from .utils import run, which


def _systemd_state(unit: str) -> str:
    return run(["systemctl", "is-active", unit], capture=True, check=False).stdout.strip()


def status(cfg: dict) -> str:
    wg = cfg.get("wireguard", {})
    mains = cfg.get("mains", {})
    routes = cfg.get("routes", {})
    parts = [
        f"Role: {cfg.get('role', 'unknown')}",
        f"Public IP: {wg.get('public_ip', '')}",
        f"Internet iface: {wg.get('internet_iface', '')}",
        f"State dir: {STATE_DIR}",
        f"Mains: {len(mains)}",
        f"Routes: {len(routes)}",
        f"WireGuard service: {_systemd_state('wg-quick@wg0')}",
        f"Reconcile timer: {_systemd_state('wgfm-reconcile.timer')}",
        f"nft rules: {'present' if RULES_FILE.exists() else 'missing'}",
    ]
    return "\n".join(parts)


def doctor() -> dict:
    checks = {
        "config_dir": STATE_DIR.exists(),
        "config": CONFIG_FILE.exists(),
        "mains": MAINS_FILE.exists(),
        "routes": ROUTES_FILE.exists(),
        "wg_conf": WG_CONF.exists(),
        "rules": RULES_FILE.exists(),
        "systemctl": which("systemctl"),
        "wg": which("wg"),
        "nft": which("nft"),
        "wg_active": _systemd_state("wg-quick@wg0") == "active",
        "timer_active": _systemd_state("wgfm-reconcile.timer") == "active",
    }
    return checks


def repair(cfg: dict) -> dict:
    from .commands import repair as _repair
    return _repair(cfg)
