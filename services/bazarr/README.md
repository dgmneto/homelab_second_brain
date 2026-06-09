# bazarr

Subtitle manager — fetches subs for sonarr/radarr libraries.

## Image
`ghcr.io/hotio/bazarr:latest` (hotio; tag not pinned)

## Access
WebUI on port **6767** (TCP+UDP via `WEBUI_PORTS=6767/tcp,6767/udp`). On `intern` at fixed IP **172.21.0.199**. Fronted by NPM (nginxIntern/nginxProd on `intern`) — proxy host config in NPM database, not repo files.

## Compose
`/home/dgmneto/homelab/services/bazarr/compose.yaml`

## Config path
`/footage/services/bazarr/config` -> `/config`

## Media paths
`/library` -> `/library` (must match sonarr/radarr paths so bazarr can write sidecar subs).

## Networks
`internalNetwork` (`intern`), static IP 172.21.0.199.

## Integrations
- **sonarr** (172.21.0.5:8989) and **radarr** (172.21.0.89:7878) -> bazarr pulls their libraries via API and downloads matching subtitles.

## Quirks / runbook
- PUID=1008, PGID=1313, UMASK=002, TZ=Europe/London.
- restart: always. No `.env`.
- `WEBUI_PORTS` is a hotio-image env that sets the served port (6767).
- `/library` path must be identical to what sonarr/radarr report or subtitle path mapping breaks.
