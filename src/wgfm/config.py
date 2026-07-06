from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from .constants import CONFIG_FILE, MAINS_FILE, ROUTES_FILE, DEFAULTS
from .errors import ConfigError
from .yamlio import dump_yaml, load_yaml
from .utils import validate_ipv4, validate_port


def default_config() -> Dict[str, Any]:
    return deepcopy(DEFAULTS)


def load_config() -> Dict[str, Any]:
    data = load_yaml(CONFIG_FILE)
    cfg = default_config()
    for k, v in data.items():
        if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    cfg.setdefault("mains", {})
    cfg.setdefault("routes", {})
    return cfg


def sync_route_views(cfg: Dict[str, Any]) -> None:
    dump_yaml(MAINS_FILE, cfg.get("mains", {}))
    dump_yaml(ROUTES_FILE, cfg.get("routes", {}))


def save_config(cfg: Dict[str, Any]) -> None:
    dump_yaml(CONFIG_FILE, cfg)
    sync_route_views(cfg)


def ensure_config() -> Dict[str, Any]:
    cfg = load_config()
    if "wireguard" not in cfg:
        cfg["wireguard"] = default_config()["wireguard"]
    cfg.setdefault("mains", {})
    cfg.setdefault("routes", {})
    return cfg


def get_main(cfg: Dict[str, Any], name: str) -> Dict[str, Any]:
    try:
        return cfg["mains"][name]
    except KeyError as exc:
        raise ConfigError(f"Main not found: {name}") from exc


def get_port_owner(cfg: Dict[str, Any], port: int) -> str | None:
    return cfg.setdefault("routes", {}).get(str(port))


def add_main(cfg: Dict[str, Any], name: str, public_ip: str, wg_ip: str, public_key: str) -> None:
    if not validate_ipv4(public_ip):
        raise ConfigError(f"Invalid public IP: {public_ip}")
    if not validate_ipv4(wg_ip):
        raise ConfigError(f"Invalid WireGuard IP: {wg_ip}")
    mains = cfg.setdefault("mains", {})
    if name in mains:
        raise ConfigError(f"Main already exists: {name}")
    mains[name] = {
        "public_ip": public_ip,
        "wg_ip": wg_ip,
        "public_key": public_key,
        "ports": [],
    }


def remove_main(cfg: Dict[str, Any], name: str) -> None:
    mains = cfg.setdefault("mains", {})
    routes = cfg.setdefault("routes", {})
    if name not in mains:
        raise ConfigError(f"Main not found: {name}")
    del mains[name]
    for port, mapped in list(routes.items()):
        if mapped == name:
            del routes[port]


def add_ports_to_main(cfg: Dict[str, Any], name: str, ports: List[int]) -> None:
    mains = cfg.setdefault("mains", {})
    routes = cfg.setdefault("routes", {})
    if name not in mains:
        raise ConfigError(f"Main not found: {name}")
    main = mains[name]
    existing = set(int(p) for p in main.get("ports", []))
    for port in ports:
        if not validate_port(str(port)):
            raise ConfigError(f"Invalid port: {port}")
        owner = routes.get(str(port))
        if owner and owner != name:
            raise ConfigError(f"Port {port} already assigned to {owner}")
        routes[str(port)] = name
        existing.add(int(port))
    main["ports"] = sorted(existing)


def remove_ports(cfg: Dict[str, Any], ports: List[int]) -> None:
    routes = cfg.setdefault("routes", {})
    mains = cfg.setdefault("mains", {})
    for port in ports:
        if not validate_port(str(port)):
            raise ConfigError(f"Invalid port: {port}")
        owner = routes.pop(str(port), None)
        if owner and owner in mains:
            mains[owner]["ports"] = [p for p in mains[owner].get("ports", []) if int(p) != port]


def move_ports(cfg: Dict[str, Any], ports: List[int], dest: str) -> None:
    mains = cfg.setdefault("mains", {})
    routes = cfg.setdefault("routes", {})
    if dest not in mains:
        raise ConfigError(f"Main not found: {dest}")
    dest_ports = {int(p) for p in mains[dest].get("ports", [])}
    for port in ports:
        if not validate_port(str(port)):
            raise ConfigError(f"Invalid port: {port}")
        old = routes.get(str(port))
        if old and old in mains:
            mains[old]["ports"] = [p for p in mains[old].get("ports", []) if int(p) != port]
        routes[str(port)] = dest
        dest_ports.add(int(port))
    mains[dest]["ports"] = sorted(dest_ports)


def list_mains(cfg: Dict[str, Any]) -> List[str]:
    return sorted(cfg.get("mains", {}).keys())


def all_routes(cfg: Dict[str, Any]) -> Dict[int, str]:
    return {int(k): v for k, v in cfg.get("routes", {}).items()}
