# Access — Prowlarr

- **URL:** https://prowlarr.intern.dgmneto.com (nginxIntern → `gluetun:9696`)
- **Credential:** `op://Homelab/Prowlarr` (user `dgmneto`). API key also in
  `/footage/services/prowlarr/config/config.xml`.
- **Auth:** app login form. User completes login.
- **Quirk:** rides the gluetun VPN namespace (`network_mode: container:gluetunProtonVPN`); the UI is
  proxied to `gluetun:9696`, not a host port. If gluetun is down, the UI is unreachable.

Reach via the Claude-in-Chrome extension (see root `../../CLAUDE.md`).
