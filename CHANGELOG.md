# Changelog

## 1.0.2
- Fixed installer ordering so WireGuard config exists before service startup.
- Made nftables cleanup safe when the table does not exist.
- Added safe backup restore extraction.
- Added immediate reconcile after config changes in the CLI.
- Made uninstall functional from the CLI and menu.
- Added validation for IPs, CIDRs, ports, and installer prompts.

# Changelog

## 1.0.0
- Initial modular release
- Front / Main management
- Multi-main port routing
- Backup / restore
- GitHub Release updater
- Auto-reconcile timer


## v0.1.10
- Add repair command to CLI and menu.
- Keep repair idempotent by re-applying sysctl, systemd units, and WireGuard state.
