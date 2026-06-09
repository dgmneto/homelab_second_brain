# plex

Plex Media Server. Streams the media library with hardware-accelerated
transcoding. Runs on its own dedicated LAN IP via a macvlan network.

## Image

- `plexinc/pms-docker:latest` — **unpinned `:latest`**.

## Access

- LAN IP: **`192.168.14.7`** (macvlan, addressable directly on the network).
- Plex server port: `32400`.
- Public/remote: `https://filmin.3e.dgmneto.com`, proxied by **Nginx Proxy Manager
  `nginxProd`** (proxy host 1) -> upstream `plex:32400`.

## Hardware acceleration / transcoding

- Device passthrough: `/dev/dri:/dev/dri` (Intel/AMD VAAPI iGPU). Host shows
  `card0` and `renderD128`, so HW transcoding is available.
- Enable "Use hardware acceleration when available" in Plex settings to use it
  (requires Plex Pass).
- Transcode cache lives under the config volume
  (`/config/Library/Application Support/Plex Media Server/Cache`).

## Paths

- Compose (server): `/home/dgmneto/homelab/services/plex/compose.yaml`
- Config: `/footage/services/plex/config` -> `/config`
- Media library: `/library/media` -> `/library/media`

## Networks

- `macVlanNetwork` (external macvlan), static `ipv4_address: 192.168.14.7`,
  gateway `192.168.14.1`.
- Because it is macvlan, Plex is reachable on the LAN as its own host but the
  Docker host itself generally cannot talk to it directly (standard macvlan
  limitation).

## Environment

- `.env` keys (values NOT recorded — `PLEX_CLAIM` is a secret token):
  - `PLEX_UID`
  - `PLEX_GID`
  - `UMASK`
  - `TZ`
  - `VERSION`
  - `PLEX_CLAIM` (commented out; one-time claim token — keep secret, never commit)

## Integrations

- `overseerr` — request frontend for Plex.
- *arr stack (`radarr`/`sonarr`/`bazarr`) populates `/library/media`.

## Quirks / runbook

- `restart: unless-stopped`.
- macvlan means no port publishing — connect via `192.168.14.7:32400` or the
  `filmin.3e.dgmneto.com` proxy, not via the host IP.
- If HW transcoding stops working, check `/dev/dri` still passes through and the
  container user is in the `render`/`video` groups.
- NEVER write the Plex claim token or auth tokens into version control.
