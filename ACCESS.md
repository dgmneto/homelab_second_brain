# Service access map — URLs and credential sources

Authoritative reverse-proxy hostnames pulled from the nginx-proxy-manager databases
(`/footage/services/nginx{Intern,Prod}/data/database.sqlite`, 2026-06-10). Reach internal hostnames
through the **Claude-in-Chrome** extension driving the user's LAN Chrome (see `CLAUDE.md`).

## Important: 1Password does NOT hold the service UI logins

The `Homelab` vault has only **four** items, all infrastructure secrets — **none is a web-UI login**:

| op item (`op://Homelab/<title>`) | What it is | NOT a UI login for |
|---|---|---|
| `Plex - Claim` | Plex server *claim* token (onboarding) | not the Plex account password |
| `ProtonVPN - Gluetun` | ProtonVPN/WireGuard creds for gluetun | — |
| `Cloudflare - DDNS` | Cloudflare API token for `ddns` | — |
| `Service Account Auth Token: Homelab` | 1Password service-account token | — |

So "log into Overseerr with a password from `op`" is not possible: Overseerr uses **Sign in with Plex**
(OAuth), and no Overseerr/sonarr/radarr/qbit credential exists in the vault. The only app password that
exists anywhere is qBittorrent's, and it is **hardcoded in `watchdog.py`** (leaked, not in op — see
`services/plex-qbittorrent-watchdog/README.md`). Logging in interactively is left to the user; this repo
maps where each credential lives, it does not perform authentication.

## Internal UIs (`nginxIntern`, `*.intern.dgmneto.com`)

| Service | URL | Upstream | Auth source |
|---|---|---|---|
| Overseerr | https://overseerr.intern.dgmneto.com | overseerr:5055 | Sign in with Plex (OAuth) |
| Plex | https://filmin.intern.dgmneto.com | plex:32400 | Plex account; `op://Homelab/Plex - Claim` = server claim only |
| Sonarr | https://sonarr.intern.dgmneto.com | sonarr:8989 | app login + API key in `/footage/services/sonarr/config/config.xml` |
| Radarr | https://radarr.intern.dgmneto.com | radarr:7878 | app login + API key in `…/radarr/config/config.xml` |
| Prowlarr | https://prowlarr.intern.dgmneto.com | gluetun:9696 | app login + API key in `…/prowlarr/config/config.xml` (rides VPN ns) |
| Bazarr | https://bazarr.intern.dgmneto.com | bazarr:6767 | app login + API key in `…/bazarr/config` |
| qBittorrent | https://qbittorrent.intern.dgmneto.com | gluetun:9090 | WebUI `admin` / password **hardcoded in watchdog.py** (rides VPN ns) |
| Home Assistant | https://ha.intern.dgmneto.com | homeassistant:8123 | HA local accounts (onboarding) |
| Zigbee2MQTT | https://z2m.intern.dgmneto.com | 192.168.14.96:8080 | frontend (auth optional) |
| NPM (internal) admin | https://nginx.intern.dgmneto.com | nginxIntern:81 | NPM admin account |
| NPM (prod) admin | https://nginxprod.intern.dgmneto.com | nginxProd:81 | NPM admin account |

## Public UIs (`nginxProd`, `*.3e.dgmneto.com`)

| Service | URL | Upstream | Auth source |
|---|---|---|---|
| Plex | https://filmin.3e.dgmneto.com | plex:32400 | Plex account (OAuth) |
| arani | https://arani.3e.dgmneto.com | arani:80 | — |
| Speedtest | https://fast.3e.dgmneto.com | speedTest:3000 | — |

## Other internal hosts seen in NPM (not yet documented under `services/`)
`dashdot`, `fast`/`speedtest`, `homarr` (192.168.14.9:7575), `home` (192.168.14.33:3000),
`netdata` (192.168.0.13:19999), `portainer` (portainer:9000), `openclaw` (192.168.11.13:18789),
`scrypted` (192.168.14.89:11080), `testvpn` (gluetun:80). Worth documenting later.

## Recommendation
If the goal is "open any service UI without hunting for passwords," add one **Login** item per app to
the `Homelab` vault (Sonarr/Radarr/Prowlarr/Bazarr/qBittorrent/NPM/HA) with its URL set, then this map
can reference `op://Homelab/<service>/password`. Today those items do not exist.
