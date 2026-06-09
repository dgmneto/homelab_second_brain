# Access — qBittorrent

- **URL:** https://qbittorrent.intern.dgmneto.com (nginxIntern → `gluetun:9090`)
- **Credential:** `op://Homelab/qbittorrent` (user `admin`).
- **Auth:** WebUI login.
- **Quirks:**
  - Rides the gluetun VPN namespace (`network_mode: container:gluetunProtonVPN`); UI proxied to
    `gluetun:9090`, no host port. Down with gluetun.
  - ⚠️ The same password is **also hardcoded in** `../plex-qbittorrent-watchdog/watchdog.py`
    (committed to the deployment repo). Rewire the watchdog to `op read` it and drop the literal,
    then rotate.

Reach via the Claude-in-Chrome extension (see root `../../CLAUDE.md`).
