from __future__ import annotations

from .constants import RULES_FILE
from .utils import atomic_write, run
from .logger import log


def render_front_rules(cfg: dict) -> str:
    wg = cfg["wireguard"]
    routes = cfg.get("routes", {})
    mains = cfg.get("mains", {})
    iface = wg.get("interface", "wg0")
    lines = [
        "table inet wg_forward {",
        "  chain prerouting {",
        "    type nat hook prerouting priority -100; policy accept;",
    ]
    for port_str, main_name in sorted(routes.items(), key=lambda x: int(x[0])):
        main = mains.get(main_name)
        if not main:
            continue
        lines.append(f'    tcp dport {port_str} dnat to {main["wg_ip"]}:{port_str}')
    lines += [
        "  }",
        "",
        "  chain forward {",
        "    type filter hook forward priority 0; policy accept;",
        "  }",
        "",
        "  chain postrouting {",
        "    type nat hook postrouting priority 100; policy accept;",
        f'    oifname "{iface}" masquerade',
        "  }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def _table_exists() -> bool:
    result = run(["nft", "list", "table", "inet", "wg_forward"], capture=True, check=False)
    return result.returncode == 0


def _delete_table_if_present() -> None:
    if _table_exists():
        run(["nft", "delete", "table", "inet", "wg_forward"], check=False)


def apply_front(cfg: dict) -> None:
    log("Applying nftables front rules")
    atomic_write(RULES_FILE, render_front_rules(cfg), 0o600)
    _delete_table_if_present()
    run(["nft", "-f", str(RULES_FILE)])
    if not cfg.get("routes"):
        log("No forwarding routes configured yet; created empty wg_forward table.")


def clear() -> None:
    log("Clearing nftables wg_forward table")
    _delete_table_if_present()
