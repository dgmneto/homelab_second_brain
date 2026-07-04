# Service access — index

Per-service access detail (URL, `op://` credential, auth method) now lives in each service's own
`services/<svc>/ACCESS.md`. This file is just the index + shared notes. Reach internal UIs through the
**Claude-in-Chrome** extension driving the user's LAN Chrome (see `CLAUDE.md`). Hostnames are
authoritative as of 2026-06-10, pulled from the NPM databases.

## UIs with an access doc

| Service | URL | Credential | Detail |
|---|---|---|---|
| Overseerr | https://overseerr.intern.dgmneto.com | Plex OAuth (none) | [services/overseerr/ACCESS.md](services/overseerr/ACCESS.md) |
| Plex | https://filmin.intern.dgmneto.com · https://filmin.3e.dgmneto.com | `op://Homelab/Plex` | [services/plex/ACCESS.md](services/plex/ACCESS.md) |
| Jellyfin | https://jellyfin.intern.dgmneto.com · https://jellyfin.3e.dgmneto.com | local account, not in op | [services/jellyfin/README.md](services/jellyfin/README.md) |
| Sonarr | https://sonarr.intern.dgmneto.com | `op://Homelab/Sonarr` | [services/sonarr/ACCESS.md](services/sonarr/ACCESS.md) |
| Radarr | https://radarr.intern.dgmneto.com | `op://Homelab/Radarr` | [services/radarr/ACCESS.md](services/radarr/ACCESS.md) |
| Prowlarr | https://prowlarr.intern.dgmneto.com | `op://Homelab/Prowlarr` | [services/prowlarr/ACCESS.md](services/prowlarr/ACCESS.md) |
| Bazarr | https://bazarr.intern.dgmneto.com | not in op | [services/bazarr/ACCESS.md](services/bazarr/ACCESS.md) |
| qBittorrent | https://qbittorrent.intern.dgmneto.com | `op://Homelab/qbittorrent` | [services/qbittorrent/ACCESS.md](services/qbittorrent/ACCESS.md) |
| Home Assistant | https://ha.intern.dgmneto.com | not in op | [services/homeassistant/ACCESS.md](services/homeassistant/ACCESS.md) |
| Zigbee2MQTT | https://z2m.intern.dgmneto.com | not in op | [services/z2mqtt/ACCESS.md](services/z2mqtt/ACCESS.md) |
| NPM (internal) | https://nginx.intern.dgmneto.com | `op://Homelab/nginx` | [services/nginxIntern/ACCESS.md](services/nginxIntern/ACCESS.md) |
| NPM (prod) | https://nginxprod.intern.dgmneto.com | `op://Homelab/NGINX Prod` | [services/nginxProd/ACCESS.md](services/nginxProd/ACCESS.md) |

## 1Password `Homelab` vault (verified 2026-06-10, 11 items)
Read a secret at run time: `op read "op://Homelab/<title>/password"` (CLI authenticates via the
desktop app; no manual signin). LOGIN items: `qbittorrent`, `Sonarr`, `Radarr`, `Prowlarr`, `Plex`,
`nginx`, `NGINX Prod`. Infra: `Plex - Claim`, `ProtonVPN - Gluetun`, `Cloudflare - DDNS`,
`Service Account Auth Token: Homelab`. Never paste a retrieved value into this repo — reference the
`op://` path. Interactive login is performed by the user, not automated.

## Other internal hosts in NPM (not yet documented under `services/`)
`dashdot`, `fast`/`speedtest`, `homarr` (192.168.14.9:7575), `home` (192.168.14.33:3000),
`netdata` (192.168.0.13:19999), `portainer` (portainer:9000), `openclaw` (192.168.11.13:18789),
`scrypted` (192.168.14.89:11080), `testvpn` (gluetun:80).

## Open items
- Add vault logins for **Bazarr**, **Home Assistant**, **Zigbee2MQTT**, **Jellyfin**.
- **qBittorrent:** password is in the vault but the same value is still hardcoded in
  `services/plex-qbittorrent-watchdog/watchdog.py` — rewire to `op read` and rotate.
