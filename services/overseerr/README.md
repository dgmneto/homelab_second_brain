# overseerr

Request/discovery frontend — users request media, routed into sonarr/radarr + Plex.

## Image
`sctx/overseerr:latest` (tag not pinned)

## Access
WebUI on port **5055** (container internal). On `intern` (dynamic IP — no static address assigned). Fronted by NPM (nginxIntern/nginxProd on `intern`) — proxy host config in NPM database, not repo files.

## Compose
`/home/dgmneto/homelab/services/overseerr/compose.yaml`

## Config path
`/footage/services/overseerr/config` -> `/app/config`

## Media paths
None (no media mounts).

## Networks
`internalNetwork` (`intern`), no static IP.

## Integrations
- **plex** -> auth + library scan / availability.
- **sonarr** (172.21.0.5:8989) -> TV requests.
- **radarr** (172.21.0.89:7878) -> movie requests.

## Quirks / runbook
- `TZ=Europe/London`, `LOG_LEVEL=debug` (verbose logging — consider lowering to `info` in prod).
- restart: always. No `.env`. No PUID/PGID set (runs as image default).
- Config dir mounts at `/app/config` (differs from the *arr `/config` convention).
