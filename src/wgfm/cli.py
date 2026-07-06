from __future__ import annotations

import argparse
import sys

from .constants import APP_VERSION
from .config import load_config, save_config, add_main, remove_main, add_ports_to_main, remove_ports, move_ports, list_mains
from .installer import install_front_interactive, install_main_interactive
from .commands import reconcile, repair, update
from .backup import create_backup, restore_backup
from .health import doctor, status
from .utils import ask_nonempty, parse_port_spec, validate_ipv4
from .uninstall import uninstall
from .errors import WGFMError, ValidationError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wgfm")
    sub = p.add_subparsers(dest="cmd")
    for cmd in [
        "install-front", "install-main", "add-main", "remove-main", "list-mains",
        "assign", "remove-ports", "move", "update-main-ip", "update-front",
        "reconcile", "repair", "status", "doctor", "backup", "restore", "update", "uninstall", "version"
    ]:
        sub.add_parser(cmd)
    return p


def _print_menu() -> None:
    print(f"WG Forward Manager {APP_VERSION}")
    print()
    print("1) Install Front")
    print("2) Install Main")
    print()
    print("3) Add Main")
    print("4) Remove Main")
    print("5) List Mains")
    print()
    print("6) Assign Ports")
    print("7) Remove Ports")
    print("8) Move Ports")
    print()
    print("9) Update Main IP")
    print("10) Update Front")
    print()
    print("11) Status")
    print("12) Doctor")
    print("13) Repair")
    print("14) Reconcile")
    print()
    print("15) Backup")
    print("16) Restore")
    print()
    print("17) Version")
    print("18) Uninstall")
    print()
    print("0) Exit")


def _prompt_ports() -> list[int]:
    specs: list[int] = []
    print("Enter ports, blank line to finish.")
    while True:
        line = input().strip()
        if not line:
            break
        specs.extend(parse_port_spec(line))
    return specs


def _apply_and_save(cfg: dict) -> None:
    save_config(cfg)
    reconcile(cfg)


def interactive_menu() -> None:
    while True:
        try:
            _print_menu()
            choice = input("Select: ").strip()
            if choice == "1":
                install_front_interactive()
                print("Front installed.")
            elif choice == "2":
                install_main_interactive()
                print("Main installed.")
            elif choice == "3":
                cfg = load_config()
                name = ask_nonempty("Main name")
                public_ip = ask_nonempty("Main public IP")
                wg_ip = ask_nonempty("Main WireGuard IP")
                public_key = ask_nonempty("Main public key")
                add_main(cfg, name, public_ip, wg_ip, public_key)
                _apply_and_save(cfg)
                print("Main added.")
            elif choice == "4":
                cfg = load_config()
                name = ask_nonempty("Main name")
                remove_main(cfg, name)
                _apply_and_save(cfg)
                print("Main removed.")
            elif choice == "5":
                print(list_mains(load_config()))
            elif choice == "6":
                cfg = load_config()
                name = ask_nonempty("Main name")
                specs = _prompt_ports()
                add_ports_to_main(cfg, name, specs)
                _apply_and_save(cfg)
                print("Ports assigned.")
            elif choice == "7":
                cfg = load_config()
                specs = _prompt_ports()
                remove_ports(cfg, specs)
                _apply_and_save(cfg)
                print("Ports removed.")
            elif choice == "8":
                cfg = load_config()
                name = ask_nonempty("Destination main")
                specs = _prompt_ports()
                move_ports(cfg, specs, name)
                _apply_and_save(cfg)
                print("Ports moved.")
            elif choice == "9":
                cfg = load_config()
                name = ask_nonempty("Main name")
                new_ip = ask_nonempty("New public IP")
                if not validate_ipv4(new_ip):
                    raise ValidationError("Invalid IPv4 address")
                mains = cfg.get("mains", {})
                if name in mains:
                    mains[name]["public_ip"] = new_ip
                    _apply_and_save(cfg)
                    print("Updated.")
                else:
                    print("Main not found.")
            elif choice == "10":
                cfg = load_config()
                cfg["front"]["public_ip"] = ask_nonempty("Front public IP")
                cfg["front"]["public_key"] = ask_nonempty("Front public key")
                _apply_and_save(cfg)
                print("Updated.")
            elif choice == "11":
                print(status(load_config()))
            elif choice == "12":
                print(doctor())
            elif choice == "13":
                print(repair(load_config()))
            elif choice == "14":
                reconcile(load_config())
                print("Reconciled.")
            elif choice == "15":
                print(create_backup())
            elif choice == "16":
                archive = ask_nonempty("Backup archive path")
                restore_backup(archive)
                print(repair(load_config()))
                print("Restored.")
            elif choice == "17":
                print(APP_VERSION)
            elif choice == "18":
                uninstall(confirm=True)
                print("Uninstalled.")
                return
            elif choice == "0":
                return
            else:
                print("Invalid choice.")
        except ValidationError as exc:
            print(f"Error: {exc}")
        except WGFMError as exc:
            print(f"Error: {exc}")
        except Exception as exc:
            print(f"Error: {exc}")
        except KeyboardInterrupt:
            print()
            return


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if not args.cmd:
            interactive_menu()
            return
        cfg = load_config()
        if args.cmd == "install-front":
            install_front_interactive()
            print("Front installed.")
        elif args.cmd == "install-main":
            install_main_interactive()
            print("Main installed.")
        elif args.cmd == "add-main":
            name = ask_nonempty("Main name")
            public_ip = ask_nonempty("Main public IP")
            wg_ip = ask_nonempty("Main WireGuard IP")
            public_key = ask_nonempty("Main public key")
            add_main(cfg, name, public_ip, wg_ip, public_key)
            _apply_and_save(cfg)
            print("Main added.")
        elif args.cmd == "remove-main":
            name = ask_nonempty("Main name")
            remove_main(cfg, name)
            _apply_and_save(cfg)
            print("Main removed.")
        elif args.cmd == "list-mains":
            print(list_mains(cfg))
        elif args.cmd == "assign":
            name = ask_nonempty("Main name")
            specs = []
            print("Enter ports, blank line to finish.")
            while True:
                line = input().strip()
                if not line:
                    break
                specs.extend(parse_port_spec(line))
            add_ports_to_main(cfg, name, specs)
            _apply_and_save(cfg)
            print("Ports assigned.")
        elif args.cmd == "remove-ports":
            specs = []
            print("Enter ports, blank line to finish.")
            while True:
                line = input().strip()
                if not line:
                    break
                specs.extend(parse_port_spec(line))
            remove_ports(cfg, specs)
            _apply_and_save(cfg)
            print("Ports removed.")
        elif args.cmd == "move":
            name = ask_nonempty("Destination main")
            specs = []
            print("Enter ports, blank line to finish.")
            while True:
                line = input().strip()
                if not line:
                    break
                specs.extend(parse_port_spec(line))
            move_ports(cfg, specs, name)
            _apply_and_save(cfg)
            print("Ports moved.")
        elif args.cmd == "update-main-ip":
            name = ask_nonempty("Main name")
            new_ip = ask_nonempty("New public IP")
            mains = cfg.get("mains", {})
            if name in mains:
                mains[name]["public_ip"] = new_ip
                _apply_and_save(cfg)
                print("Updated.")
            else:
                print("Main not found.")
        elif args.cmd == "update-front":
            front_ip = ask_nonempty("Front public IP")
            if not validate_ipv4(front_ip):
                raise ValidationError("Invalid IPv4 address")
            cfg["front"]["public_ip"] = front_ip
            cfg["front"]["public_key"] = ask_nonempty("Front public key")
            _apply_and_save(cfg)
            print("Updated.")
        elif args.cmd == "reconcile":
            reconcile(cfg)
            print("Reconciled.")
        elif args.cmd == "repair":
            print(repair(cfg))
        elif args.cmd == "status":
            print(status(cfg))
        elif args.cmd == "doctor":
            print(doctor())
        elif args.cmd == "backup":
            print(create_backup())
        elif args.cmd == "restore":
            archive = ask_nonempty("Backup archive path")
            restore_backup(archive)
            print(repair(load_config()))
            print("Restored.")
        elif args.cmd == "update":
            print(update())
        elif args.cmd == "uninstall":
            uninstall(confirm=True)
            print("Uninstalled.")
        elif args.cmd == "version":
            print(APP_VERSION)
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except WGFMError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
