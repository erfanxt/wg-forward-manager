#!/usr/bin/env bash
set -Eeuo pipefail

REPO_OWNER="erfanxt"
REPO_NAME="wg-forward-manager"
BRANCH="main"
INSTALL_DIR="/opt/wg-forward-manager"
BIN_LINK="/usr/local/bin/wgfm"

log(){ printf '[*] %s
' "$*"; }
die(){ printf '[x] %s
' "$*" >&2; exit 1; }

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  die "Run as root: sudo bash install.sh"
fi

if ! command -v systemctl >/dev/null 2>&1; then
  die "systemctl is required. Use a systemd-based Ubuntu server."
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y wireguard nftables python3 python3-yaml curl ca-certificates tar gzip

tmpdir="$(mktemp -d)"
cleanup(){ rm -rf "$tmpdir"; }
trap cleanup EXIT

source_root=""
case "$0" in
  bash|-bash)
    source_root=""
    ;;
  *)
    if [[ -f "$0" ]]; then
      source_root="$(cd "$(dirname "$0")" && pwd)"
    fi
    ;;
esac

copy_tree() {
  local src="$1" dst="$2"
  rm -rf "$dst"
  mkdir -p "$dst"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete       --exclude '.git'       --exclude '__pycache__'       --exclude '*.pyc'       "$src"/ "$dst"/
  else
    cp -a "$src"/. "$dst"/
    find "$dst" -type d \( -name '.git' -o -name '__pycache__' \) -prune -exec rm -rf {} + 2>/dev/null || true
    find "$dst" -name '*.pyc' -delete 2>/dev/null || true
  fi
}

if [[ -n "$source_root" && -f "$source_root/wgfm" && -d "$source_root/src" ]]; then
  log "Installing from local source tree..."
  copy_tree "$source_root" "$INSTALL_DIR"
else
  log "Downloading source archive from GitHub..."
  archive="$tmpdir/main.tar.gz"
  curl -fsSL "https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz" -o "$archive"
  tar -xzf "$archive" -C "$tmpdir"
  extracted="$(find "$tmpdir" -maxdepth 1 -type d -name "${REPO_NAME}-${BRANCH}" | head -n 1)"
  [[ -n "$extracted" ]] || die "Could not extract repository archive."
  copy_tree "$extracted" "$INSTALL_DIR"
fi

install -d -m 700 /etc/wg-forward /etc/wireguard /var/log
chmod 755 "$INSTALL_DIR/wgfm" "$INSTALL_DIR/install.sh" "$INSTALL_DIR/update.sh" "$INSTALL_DIR/uninstall.sh" 2>/dev/null || true
ln -sfn "$INSTALL_DIR/wgfm" "$BIN_LINK"

log "Installed wgfm to $BIN_LINK"
log "Run: wgfm"
