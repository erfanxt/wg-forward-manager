from __future__ import annotations

from .constants import WG_CONF, WG_IFACE
from .utils import run, atomic_write
from .logger import log


def _gen_keypair() -> tuple[str, str]:
    import subprocess
    priv = subprocess.check_output(["wg", "genkey"], text=True).strip()
    pub = subprocess.check_output(["wg", "pubkey"], text=True, input=priv).strip()
    return priv, pub


def ensure_front_keys(cfg: dict) -> dict:
    front = cfg.setdefault("front", {})
    if not front.get("private_key") or not front.get("public_key"):
        log("Generating front WireGuard keypair")
        priv, pub = _gen_keypair()
        front["private_key"] = priv
        front["public_key"] = pub
    return cfg


def ensure_node_keys(cfg: dict) -> dict:
    node = cfg.setdefault("node", {})
    if not node.get("private_key") or not node.get("public_key"):
        log("Generating node WireGuard keypair")
        priv, pub = _gen_keypair()
        node["private_key"] = priv
        node["public_key"] = pub
    return cfg


def render_front_conf(cfg: dict) -> str:
    wg = cfg["wireguard"]
    front = cfg["front"]
    lines = [
        "[Interface]",
        f'Address = {wg["front_wg_ip"]}/{wg["prefix"]}',
        f'ListenPort = {wg["port"]}',
        f'PrivateKey = {front["private_key"]}',
        f'MTU = {wg["mtu"]}',
        "",
    ]
    for name, main in sorted(cfg.get("mains", {}).items()):
        lines += [
            "[Peer]",
            f'PublicKey = {main["public_key"]}',
            f'Endpoint = {main["public_ip"]}:{wg["port"]}',
            f'AllowedIPs = {main["wg_ip"]}/32',
            "PersistentKeepalive = 25",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_main_conf(cfg: dict) -> str:
    wg = cfg["wireguard"]
    front = cfg["front"]
    node = cfg["node"]
    lines = [
        "[Interface]",
        f'Address = {wg["main_wg_ip"]}/{wg["prefix"]}',
        f'ListenPort = {wg["port"]}',
        f'PrivateKey = {node["private_key"]}',
        f'MTU = {wg["mtu"]}',
        "",
        "[Peer]",
        f'PublicKey = {front["public_key"]}',
        f'Endpoint = {front["public_ip"]}:{wg["port"]}',
        f'AllowedIPs = {wg["front_wg_ip"]}/32',
        "PersistentKeepalive = 25",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def apply_front(cfg: dict) -> None:
    log("Applying front WireGuard configuration")
    atomic_write(WG_CONF, render_front_conf(cfg), 0o600)
    run(["systemctl", "restart", f"wg-quick@{WG_IFACE}"])


def apply_main(cfg: dict) -> None:
    log("Applying main WireGuard configuration")
    atomic_write(WG_CONF, render_main_conf(cfg), 0o600)
    run(["systemctl", "restart", f"wg-quick@{WG_IFACE}"])
