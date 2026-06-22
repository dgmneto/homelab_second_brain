# prowlarr

Indexer manager/proxy — feeds indexer definitions and search to sonarr/radarr.

## Image
`lscr.io/linuxserver/prowlarr:latest` (LinuxServer; tag not pinned)

## Access
WebUI on port **9696**. Container on `internalNetwork` (`intern`), own IP (e.g. `172.21.0.8`). Fronted by NPM (nginxIntern) — proxy host `prowlarr.intern.dgmneto.com` → `prowlarr:9696`.

## Compose
`/home/dgmneto/homelab/services/prowlarr/compose.yaml`

## Config path
`/footage/services/prowlarr/config` -> `/config`

## Media paths
None (indexer manager, no media mounts).

## Networks
Directly on `internalNetwork` (`172.21.0.0/24`). Indexer traffic egresses via host internet (no VPN). VPN is not needed for prowlarr — it queries indexers over HTTPS and VPN exit IPs were blocking some trackers.

## Integrations
- Pushes indexer configs to **sonarr** and **radarr** (Prowlarr -> *arr "Apps" sync).

## Quirks / runbook
- PUID=1004, PGID=1313, UMASK=002, TZ=Europe/London.
- restart: always.
- Healthcheck: `curl -f https://www.google.com` every 15s.
- Previously ran in gluetun's network namespace (`network_mode: container:gluetunProtonVPN`) — removed 2026-06-22 because VPN was blocking tracker IPs.
- No `.env` file.
