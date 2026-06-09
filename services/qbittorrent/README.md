# qbittorrent

BitTorrent client (LinuxServer.io build). **All traffic is forced through the
ProtonVPN tunnel** provided by the `gluetunProtonVPN` container.

## VPN routing (IMPORTANT)

- Compose sets `network_mode: container:gluetunProtonVPN`. qbittorrent has **no
  network namespace of its own** — it shares gluetun's. Every connection
  (trackers, peers, WebUI) goes through ProtonVPN.
- Because of this, qbittorrent **publishes no ports itself**. Its WebUI port
  `9090` (`WEBUI_PORT=9090`) lives in gluetun's namespace.
- **If `gluetunProtonVPN` is down, qbittorrent has zero connectivity.** Start
  order matters: gluetun must be up first.
- ProtonVPN port forwarding (configured in gluetun) is pushed into qbittorrent via
  gluetun's `VPN_PORT_FORWARDING_UP_COMMAND` so inbound peer connections work.
- A `plex-qbittorrent-watchdog` service exists in the stack (likely restarts
  qbittorrent when the forwarded port / VPN changes).

## Image

- `lscr.io/linuxserver/qbittorrent:latest` — **unpinned `:latest`**.

## Access

- WebUI: `http://qbittorrent.intern.dgmneto.com` (internal only).
- Proxied by **Nginx Proxy Manager `nginxIntern`** (proxy host 8) to upstream
  `gluetun:9090` — NOT to the qbittorrent container directly, because the port
  lives in gluetun's namespace.
- Container status: `Up (healthy)`; healthcheck curls `https://www.google.com`
  through the tunnel to confirm VPN connectivity.

## Paths

- Compose (server): `/home/dgmneto/homelab/services/qbittorrent/compose.yaml`
- Config: `/footage/services/qbittorrent/config` -> `/config`
- Torrents: `/library/torrent` -> `/library/torrent` (same path inside container)

## Environment

- `PUID=1302`, `PGID=1313`, `UMASK=002`, `TZ=Europe/London`, `WEBUI_PORT=9090`.

## Networks

- None of its own — inherits `internalNetwork` via gluetun's namespace.

## Integrations

- `gluetunProtonVPN` — network provider (hard dependency).
- `prowlarr` / `radarr` / `sonarr` / `bazarr` — indexer + *arr stack feed
  downloads here.
- `plex-qbittorrent-watchdog` — monitors/restarts qbittorrent.

## Quirks / runbook

- `restart: always`.
- If WebUI is unreachable, first check gluetun health (`docker ps`), not
  qbittorrent.
- The healthcheck failing usually means the VPN tunnel dropped, not that
  qbittorrent crashed.
- Paths `/library/torrent` are identical host/container — keep that mapping for the
  *arr stack hardlink/move logic to work.
