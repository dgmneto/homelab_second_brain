# radarr

Movie PVR — searches, grabs and organizes films.

## Image
`ghcr.io/hotio/radarr:latest` (hotio; tag not pinned)

## Access
WebUI on port **7878** (container internal). On `intern` at fixed IP **172.21.0.89**. Fronted by NPM (nginxIntern/nginxProd on `intern`) — proxy host config in NPM database, not repo files.

## Compose
`/home/dgmneto/homelab/services/radarr/compose.yaml`

## Config path
`/footage/services/radarr/config` -> `/config`

## Media paths
`/library` -> `/library` (full media tree; shared with sonarr, bazarr, qbittorrent).

## Networks
`internalNetwork` (`intern`), static IP 172.21.0.89.

## Integrations
- **prowlarr** -> supplies indexers (Prowlarr app sync).
- **qbittorrent** -> download client.
- **bazarr** -> reads radarr library/API for subtitles.
- **overseerr** -> sends movie requests into radarr.

## Quirks / runbook
- PUID=1007, PGID=1313, UMASK=002, TZ=Europe/London.
- restart: always. No `.env`.
- `/library` mounted at the same path inside and out — keep paths consistent with sonarr/qbittorrent for hardlinks.
