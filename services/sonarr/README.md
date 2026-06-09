# sonarr

TV series PVR — searches, grabs and organizes episodes.

## Image
`ghcr.io/hotio/sonarr:latest` (hotio; tag not pinned)

## Access
WebUI on port **8989** (container internal). On `intern` at fixed IP **172.21.0.5**. Fronted by NPM (nginxIntern/nginxProd on `intern`) — proxy host config in NPM database, not repo files.

## Compose
`/home/dgmneto/homelab/services/sonarr/compose.yaml`

## Config path
`/footage/services/sonarr/config` -> `/config`

## Media paths
`/library` -> `/library` (full media tree; shared with radarr, bazarr, qbittorrent).

## Networks
`internalNetwork` (`intern`), static IP 172.21.0.5.

## Integrations
- **prowlarr** -> supplies indexers (Prowlarr app sync).
- **qbittorrent** -> download client.
- **bazarr** -> reads sonarr library/API for subtitles.
- **overseerr** -> sends TV requests into sonarr.

## Quirks / runbook
- PUID=1301, PGID=1313, UMASK=002, TZ=Europe/London.
- restart: always. No `.env`.
- `/library` is mounted at the same path inside and out — keep import/download paths consistent across sonarr/radarr/qbittorrent for hardlinks.
