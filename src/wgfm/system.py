from __future__ import annotations

from pathlib import Path

from .constants import INSTALL_DIR, INSTALL_BIN, RECONCILE_SERVICE, RECONCILE_TIMER, WG_IFACE
from .utils import run


def install_system_files() -> None:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    INSTALL_BIN.parent.mkdir(parents=True, exist_ok=True)


def enable_services() -> None:
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", f"wg-quick@{WG_IFACE}"])
    run(["systemctl", "enable", "wgfm-reconcile.timer"])
    run(["systemctl", "start", "wgfm-reconcile.timer"])


def write_sysctl_forwarding() -> None:
    path = Path("/etc/sysctl.d/99-wg-forward.conf")
    path.write_text("net.ipv4.ip_forward=1\n", encoding="utf-8")
    run(["sysctl", "--system"])


def write_systemd_units(script_path: str) -> None:
    RECONCILE_SERVICE.write_text(f"""[Unit]
Description=WG Forward Manager reconcile
After=network-online.target wg-quick@{WG_IFACE}.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart={script_path} reconcile
""", encoding="utf-8")
    RECONCILE_TIMER.write_text("""[Unit]
Description=WG Forward Manager reconcile timer

[Timer]
OnBootSec=20
OnUnitActiveSec=60
Persistent=true
Unit=wgfm-reconcile.service

[Install]
WantedBy=timers.target
""", encoding="utf-8")
