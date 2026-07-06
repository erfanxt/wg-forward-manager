from pathlib import Path

APP_NAME = "WG Forward Manager"
APP_VERSION = "1.0.3"
REPO_OWNER = "erfanxt"
REPO_NAME = "wg-forward-manager"

STATE_DIR = Path("/etc/wg-forward")
CONFIG_FILE = STATE_DIR / "config.yaml"
MAINS_FILE = STATE_DIR / "mains.yaml"
ROUTES_FILE = STATE_DIR / "routes.yaml"
RULES_FILE = STATE_DIR / "wg-forward.nft"
LOG_FILE = Path("/var/log/wgfm.log")

WG_DIR = Path("/etc/wireguard")
WG_IFACE = "wg0"
WG_CONF = WG_DIR / f"{WG_IFACE}.conf"

SYSTEMD_DIR = Path("/etc/systemd/system")
RECONCILE_SERVICE = SYSTEMD_DIR / "wgfm-reconcile.service"
RECONCILE_TIMER = SYSTEMD_DIR / "wgfm-reconcile.timer"

INSTALL_DIR = Path("/opt/wg-forward-manager")
INSTALL_BIN = Path("/usr/local/bin/wgfm")

DEFAULTS = {
    "version": 1,
    "role": "",
    "wireguard": {
        "port": 51820,
        "cidr": "10.100.0.0/24",
        "prefix": 24,
        "mtu": 1420,
        "interface": WG_IFACE,
        "internet_iface": "",
        "public_ip": "",
        "front_wg_ip": "10.100.0.1",
        "main_wg_ip": "10.100.0.2",
    },
    "front": {
        "public_ip": "",
        "public_key": "",
        "private_key": "",
    },
    "node": {
        "public_key": "",
        "private_key": "",
    },
    "mains": {},
    "routes": {},
}
