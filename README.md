# WG Forward Manager

Enterprise WireGuard forwarding manager for one Front VPS and multiple Main VPS servers.

## What it does

- One Front VPS, many Main VPS servers
- Per-port forwarding over WireGuard
- YAML-based state
- Auto-recovery after reboot
- Backup / restore
- Update from latest GitHub Release
- No UFW / Fail2Ban integration

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/erfanxt/wg-forward-manager/main/install.sh | sudo bash
```

Then run:

```bash
wgfm
```

## Commands

```bash
wgfm install-front
wgfm install-main
wgfm add-main
wgfm remove-main
wgfm list-mains
wgfm assign
wgfm remove-ports
wgfm move
wgfm update-main-ip
wgfm update-front
wgfm reconcile
wgfm status
wgfm doctor
wgfm repair
wgfm backup
wgfm restore
wgfm update
wgfm uninstall
wgfm version
```

## Config

Main config file:

`/etc/wg-forward/config.yaml`

Example:

```yaml
version: 1
role: front
wireguard:
  port: 51820
  cidr: 10.100.0.0/24
  prefix: 24
  mtu: 1420
  interface: wg0
  internet_iface: ens3
  public_ip: 1.2.3.4
  front_wg_ip: 10.100.0.1
  main_wg_ip: 10.100.0.2
front:
  public_ip: 1.2.3.4
  public_key: ""
  private_key: ""
mains:
  germany:
    public_ip: 5.6.7.8
    wg_ip: 10.100.0.2
    public_key: ""
    ports: [3030, 3031]
routes:
  3030: germany
  3031: germany
```

## Typical flow

1. Install on Front.
2. Install on each Main.
3. Add the Main to Front.
4. Assign ports.
5. Let the reconcile timer and the repair command keep everything healthy after reboot.

## License

MIT
