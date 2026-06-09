# Service access map — URLs and credential sources

Authoritative reverse-proxy hostnames pulled from the nginx-proxy-manager databases
(`/footage/services/nginx{Intern,Prod}/data/database.sqlite`, 2026-06-10). Reach internal hostnames
through the **Claude-in-Chrome** extension driving the user's LAN Chrome (see `CLAUDE.md`).

## 1Password vault `Homelab` (verified 2026-06-10)

Now holds **11** items — UI logins were added. Read a password at run time with
`op read "op://Homelab/<title>/password"` (username field too). Verified `op` access works (could read
usernames and confirm password fields are set). Interactive login itself is still left to the user — this
repo references credentials, it does not authenticate.

**LOGIN items** (username in parens): `qbittorrent` (admin), `Sonarr` (dgmneto), `Radarr` (dgmneto),
`Prowlarr` (dgmneto), `Plex` (dgmneto@gmail.com), `nginx` (intern NPM admin, dgmneto@gmail.com),
`NGINX Prod` (dgmneto@gmail.com).
**Infra secrets:** `Plex - Claim`, `ProtonVPN - Gluetun`, `Cloudflare - DDNS`,
`Service Account Auth Token: Homelab`.

Still **not** in the vault: Bazarr, Home Assistant, Zigbee2MQTT. Overseerr needs none (Sign in with Plex).

## Internal UIs (`nginxIntern`, `*.intern.dgmneto.com`)

| Service | URL | Upstream | Credential (`op://Homelab/…`) |
|---|---|---|---|
| Overseerr | https://overseerr.intern.dgmneto.com | overseerr:5055 | Sign in with Plex (OAuth) — none |
| Plex | https://filmin.intern.dgmneto.com | plex:32400 | `Plex` (account login); `Plex - Claim` = server claim only |
| Sonarr | https://sonarr.intern.dgmneto.com | sonarr:8989 | `Sonarr` (user dgmneto); API key also in `…/sonarr/config/config.xml` |
| Radarr | https://radarr.intern.dgmneto.com | radarr:7878 | `Radarr` (user dgmneto); API key in `…/radarr/config/config.xml` |
| Prowlarr | https://prowlarr.intern.dgmneto.com | gluetun:9696 | `Prowlarr` (user dgmneto); rides VPN ns |
| Bazarr | https://bazarr.intern.dgmneto.com | bazarr:6767 | not in op; app login + API key in `…/bazarr/config` |
| qBittorrent | https://qbittorrent.intern.dgmneto.com | gluetun:9090 | `qbittorrent` (user admin); also still hardcoded in watchdog.py — reconcile |
| Home Assistant | https://ha.intern.dgmneto.com | homeassistant:8123 | not in op; HA local accounts |
| Zigbee2MQTT | https://z2m.intern.dgmneto.com | 192.168.14.96:8080 | not in op; frontend (auth optional) |
| NPM (internal) admin | https://nginx.intern.dgmneto.com | nginxIntern:81 | `nginx` |
| NPM (prod) admin | https://nginxprod.intern.dgmneto.com | nginxProd:81 | `NGINX Prod` |

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

## Open items
- Add vault logins for **Bazarr**, **Home Assistant**, **Zigbee2MQTT** to complete coverage.
- **qBittorrent:** password now in vault (`op://Homelab/qbittorrent`) but the same value is still
  hardcoded in `watchdog.py`. Rewire the watchdog to `op read` it (or inject via env) and drop the
  literal, then rotate.
