# Architecture

- Front VPS receives public traffic.
- WireGuard tunnel carries traffic to one or more Main VPS servers.
- nftables on Front performs TCP DNAT to each Main WireGuard IP.
