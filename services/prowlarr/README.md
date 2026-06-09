# prowlarr

Indexer manager/proxy — feeds indexer definitions and search to sonarr/radarr.

## Image
`lscr.io/linuxserver/prowlarr:latest` (LinuxServer; tag not pinned)

## Access
WebUI on port **9696**. Container runs in gluetun's network namespace (`network_mode: container:gluetunProtonVPN`), so it has **no own ports** and is reachable only via gluetun's `intern` IP. Fronted by NPM (nginxIntern/nginxProd, both on `intern` network) — proxy host config lives in the NPM database, not in repo files.

## Compose
`/home/dgmneto/homelab/services/prowlarr/compose.yaml`

## Config path
`/footage/services/prowlarr/config` -> `/config`

## Media paths
None (indexer manager, no media mounts).

## Networks
Inherits gluetun's networking via `network_mode: container:gluetunProtonVPN`. gluetun itself sits on `internalNetwork` (`intern`). All indexer traffic egresses through the ProtonVPN tunnel.

## Integrations
- Pushes indexer configs to **sonarr** and **radarr** (Prowlarr -> *arr "Apps" sync).
- Search/grab requests route out through **gluetunProtonVPN** (VPN).

## Quirks / runbook
- PUID=1004, PGID=1313, UMASK=002, TZ=Europe/London.
- restart: always.
- Healthcheck: `curl -f https://www.google.com` every 15s — verifies VPN egress is up, not the app itself. If gluetun drops, prowlarr loses all networking.
- Because it shares gluetun's netns, restarting/recreating gluetun takes prowlarr down with it; recreate prowlarr after gluetun.
- No `.env` file.
