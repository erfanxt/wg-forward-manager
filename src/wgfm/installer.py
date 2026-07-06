from __future__ import annotations

import ipaddress

from .config import ensure_config, save_config
from .wireguard import ensure_front_keys, ensure_node_keys, apply_front, apply_main
from .nftables import apply_front as apply_front_nft
from .system import write_sysctl_forwarding, write_systemd_units, enable_services
from .utils import ask, ask_nonempty, get_public_ip, get_default_iface, validate_ipv4
from .constants import INSTALL_DIR
from .logger import log


def _ask_int(prompt: str, default: int, minimum: int, maximum: int) -> int:
    while True:
        raw = ask(prompt, str(default))
        try:
            value = int(raw)
        except ValueError:
            print(f"Please enter a number between {minimum} and {maximum}.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Please enter a number between {minimum} and {maximum}.")


def _ask_cidr(prompt: str, default: str) -> tuple[str, int]:
    while True:
        raw = ask(prompt, default).strip()
        try:
            net = ipaddress.ip_network(raw, strict=False)
        except ValueError:
            print("Please enter a valid CIDR, e.g. 10.100.0.0/24")
            continue
        return str(net), net.prefixlen


def _ask_ipv4(prompt: str, default: str | None = None) -> str:
    while True:
        value = ask_nonempty(prompt, default).strip()
        if not validate_ipv4(value):
            print("Please enter a valid IPv4 address.")
            continue
        return value


def common_wireguard_prompts(cfg: dict) -> None:
    wg = cfg["wireguard"]
    wg["port"] = _ask_int("WireGuard port", int(wg["port"]), 1, 65535)
    cidr, prefix = _ask_cidr("WireGuard network CIDR", str(wg["cidr"]))
    wg["cidr"] = cidr
    wg["prefix"] = prefix
    wg["front_wg_ip"] = _ask_ipv4("Front WireGuard IP", str(wg["front_wg_ip"]))
    wg["main_wg_ip"] = _ask_ipv4("Main WireGuard IP", str(wg["main_wg_ip"]))
    wg["mtu"] = _ask_int("WireGuard MTU", int(wg["mtu"]), 576, 9000)


def _print_install_summary(cfg: dict) -> None:
    wg = cfg["wireguard"]
    role = cfg.get("role", "unknown")
    print()
    print("========================================")
    print(f"{role.title()} installation completed successfully")
    print("========================================")
    print()
    if role == "front":
        print("Front Public Key:")
        print(cfg["front"]["public_key"])
        print()
        print(f"WireGuard Address: {wg['front_wg_ip']}/{wg['prefix']}")
        print(f"Listen Port      : {wg['port']}")
        print("Config File      : /etc/wg-forward/config.yaml")
        print(f"Launcher         : {INSTALL_DIR / 'wgfm'}")
        print()
        if cfg.get("routes"):
            print("Forwarding rules are ready.")
        else:
            print("No forwarding rules yet.")
            print("Add a Main and assign ports to create nftables rules.")
    elif role == "main":
        print("Main Public Key:")
        print(cfg["node"]["public_key"])
        print()
        print(f"WireGuard Address: {wg['main_wg_ip']}/{wg['prefix']}")
        print(f"Listen Port      : {wg['port']}")
        print(f"Front IP         : {cfg['front']['public_ip']}")
        print()
        print("Next step:")
        print("Return to the Front server and Add Main / Assign Ports.")
    print()


def install_front_interactive() -> dict:
    log("Starting front installation")
    cfg = ensure_config()
    cfg["role"] = "front"
    cfg["wireguard"]["public_ip"] = get_public_ip() or _ask_ipv4("Front public IP")
    cfg["wireguard"]["internet_iface"] = get_default_iface() or ask_nonempty("Internet interface")
    common_wireguard_prompts(cfg)
    ensure_front_keys(cfg)
    save_config(cfg)
    write_sysctl_forwarding()
    write_systemd_units(str(INSTALL_DIR / "wgfm"))
    apply_front(cfg)
    apply_front_nft(cfg)
    enable_services()
    save_config(cfg)
    _print_install_summary(cfg)
    log("Front installation completed")
    return cfg


def install_main_interactive() -> dict:
    log("Starting main installation")
    cfg = ensure_config()
    cfg["role"] = "main"
    cfg["wireguard"]["public_ip"] = get_public_ip() or _ask_ipv4("This server public IP")
    cfg["wireguard"]["internet_iface"] = get_default_iface() or ask_nonempty("Internet interface")
    common_wireguard_prompts(cfg)
    cfg["front"]["public_ip"] = _ask_ipv4("Front public IP")
    cfg["front"]["public_key"] = ask_nonempty("Front public key")
    ensure_node_keys(cfg)
    save_config(cfg)
    write_sysctl_forwarding()
    write_systemd_units(str(INSTALL_DIR / "wgfm"))
    apply_main(cfg)
    enable_services()
    save_config(cfg)
    _print_install_summary(cfg)
    log("Main installation completed")
    return cfg
