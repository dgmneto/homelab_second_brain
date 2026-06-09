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
- Torrents auto-pause while Plex is streaming: the host-side `systemd --user` service
  **plex-qbittorrent-watchdog** stops/starts torrents via `docker exec` based on Plex
  sessions. If downloads stall during playback (or never resume), check that service.
  See `../plex-qbittorrent-watchdog/README.md`.

### Runbook: "downloads are all paused / stopped"

Fast path (verified 2026-06-10). **First step for any UI service: open the WebUI via
Claude-in-Chrome** — torrent state is visible instantly there; server logs do not show it.

1. **Open WebUI:** `switch_browser` → `tabs_context_mcp` → `navigate
   https://qbittorrent.intern.dgmneto.com`. No login (NPM-only, no app auth).
   `read_page` overflows the 50k char limit — use `computer` **screenshot** instead.
2. **Read bottom status bar** (zoom region ~`[900,573,1320,596]`):
   - **green globe** = peer/VPN connectivity OK. orange = no connection → gluetun down.
   - **blue** speed-limiter icon = normal rate. orange = alt-speed throttling.
   - "Free space: N GiB" = disk fine. Left sidebar gives instant
     `All / Downloading / Stopped / Errored` counts.
3. **Decision table:**
   | Symptom | Cause | Fix |
   |---|---|---|
   | orange globe, 0 peers | gluetun/VPN down | check `docker ps` gluetun first |
   | all `Stopped`, green globe, **0 B / 0%** | mass stop after a `watchtower` restart (unpinned `:latest`, 30s poll, recreates container → torrents return stopped) | select all → Resume |
   | some `Stopped`, others mid-%, during/after Plex playback | **plex-qbittorrent-watchdog** stopped active torrents and didn't resume (crashed / lost state) → `journalctl --user -u plex-qbittorrent-watchdog` | restart watchdog; it only resumes hashes IT stopped |
   | `Errored` torrents | missing files / moved disk | per-torrent recheck |
   | green globe, torrents `Downloading` but 0 B/s | no VPN port-forward / stalled peers | check gluetun port-forward |
4. **Rule out config auto-pause:** Tools → Options → Downloads → "Do not start the
   download automatically" + "Torrent stop condition" (as of 2026-06-10 both OFF/None,
   so newly-added torrents are NOT expected to be stopped).
5. Confirm watchtower restart theory: `docker logs qbittorrent | head` → `Build-date:`
   vs outage time. Watchdog only stops *active* torrents, so all-`Stopped`-at-0B is the
   restart signature, not the watchdog.
