from __future__ import annotations
import os, re, shutil, socket, subprocess, urllib.request
from pathlib import Path
from typing import Iterable, List, Sequence
from .errors import ValidationError

def ensure_root() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Run this command as root (sudo).")

def run(cmd: Sequence[str], *, capture: bool = False, check: bool = True, cwd: str | None = None) -> subprocess.CompletedProcess:
    kwargs = {"check": check, "text": True, "cwd": cwd}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    return subprocess.run(list(cmd), **kwargs)

def shell(command: str, *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    return run(["bash", "-lc", command], capture=capture, check=check)

def which(name: str) -> bool:
    return shutil.which(name) is not None

def ask(prompt: str, default: str | None = None) -> str:
    if default is None or default == "":
        return input(f"{prompt}: ").strip()
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default

def ask_nonempty(prompt: str, default: str | None = None) -> str:
    while True:
        value = ask(prompt, default).strip()
        if value:
            return value
        print("Value cannot be empty.")

def ask_yes_no(prompt: str, default: str = "no") -> bool:
    while True:
        value = ask(prompt, default).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer yes or no.")

def validate_ipv4(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False

def validate_port(value: str) -> bool:
    return value.isdigit() and 1 <= int(value) <= 65535

def get_public_ip() -> str:
    for url in ("https://api.ipify.org", "https://ifconfig.me"):
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                ip = resp.read().decode().strip()
                if validate_ipv4(ip):
                    return ip
        except Exception:
            pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return ""

def get_default_iface() -> str:
    try:
        out = run(["ip", "route", "show", "default"], capture=True).stdout or ""
        for line in out.splitlines():
            parts = line.split()
            if "dev" in parts:
                return parts[parts.index("dev") + 1]
    except Exception:
        pass
    return ""

def atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.chmod(tmp, mode)
    tmp.replace(path)

def unique_sorted(items: Iterable[str]) -> List[str]:
    out = []
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return sorted(out, key=lambda x: int(x) if x.isdigit() else x)

def parse_port_spec(spec: str) -> List[int]:
    """
    Parse a single expression or a comma-separated list of expressions.
    Supported examples:
      3030
      3030-3035
      3030,3031,3039
      3030-3035,3040,3050-3052
    """
    result: List[int] = []
    for chunk in (part.strip() for part in spec.split(",")):
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            if not (validate_port(a) and validate_port(b)):
                raise ValidationError(f"Invalid port range: {chunk}")
            start, end = int(a), int(b)
            if start > end:
                raise ValidationError(f"Invalid port range: {chunk}")
            result.extend(range(start, end + 1))
        else:
            if not validate_port(chunk):
                raise ValidationError(f"Invalid port: {chunk}")
            result.append(int(chunk))
    if not result:
        raise ValidationError("Empty port specification")
    return [int(p) for p in unique_sorted(str(p) for p in result)]
