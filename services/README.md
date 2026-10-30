# services/

One subfolder per homelab service, flat regardless of host. Each holds notes, ports, config paths, and
runbooks for that service. The machine it runs on is documented under [../hosts/](../hosts/).

- **casaos** services: compose files live on the server at
  `/home/dgmneto/homelab/services/<svc>/compose.yaml` (separate repo `dgmneto/homelab`), not here.
- **homelab-notebook** services: NixOS modules in [../hosts/homelab-notebook/nixos/](../hosts/homelab-notebook/nixos/)
  (in this repo).

This is the knowledge layer.

## Service → host

| Service | Host | Kind |
|---|---|---|
| [arr-maintenance](arr-maintenance/README.md) | casaos | host cron jobs |
| [autoheal](autoheal/README.md) | casaos | docker |
| [bazarr](bazarr/README.md) | casaos | docker |
| [ddns](ddns/README.md) | casaos | docker |
| [gluetunProtonVPN](gluetunProtonVPN/README.md) | casaos | docker |
| [hermes](hermes/README.md) | **homelab-notebook** | NixOS module (casaos containers stopped, rollback only) |
| [homeassistant](homeassistant/README.md) | casaos | docker |
| [jellyfin](jellyfin/README.md) | casaos | docker |
| [matter](matter/README.md) | **homelab-notebook** | NixOS module (since 2026-10-30) |
| [mosquitto](mosquitto/README.md) | **homelab-notebook** | NixOS module (since 2026-10-30) |
| [nginxIntern](nginxIntern/README.md) | casaos | docker |
| [nginxProd](nginxProd/README.md) | casaos | docker |
| [overseerr](overseerr/README.md) | casaos | docker |
| [pihole](pihole/README.md) | **homelab-notebook** | NixOS module (tailnet ad-blocking DNS) |
| [plex](plex/README.md) | casaos | docker |
| [plex-qbittorrent-watchdog](plex-qbittorrent-watchdog/README.md) | casaos | `systemd --user` unit |
| [prowlarr](prowlarr/README.md) | casaos | docker (gluetun netns) |
| [qbittorrent](qbittorrent/README.md) | casaos | docker (gluetun netns) |
| [radarr](radarr/README.md) | casaos | docker |
| [sonarr](sonarr/README.md) | casaos | docker |
| [tailscale](tailscale/README.md) | casaos + **homelab-notebook** | casaos: native apt + systemd (not docker); notebook: NixOS module |
| [terminus](terminus/README.md) | casaos | docker |
| [trmnl-ai](trmnl-ai/README.md) | casaos | docker (LLM-designed TRMNL screen for terminus) |
| [watchtower](watchtower/README.md) | casaos | docker |
| [z2mqtt](z2mqtt/README.md) | **homelab-notebook** | NixOS module (since 2026-10-30) |

Adding a service: new folder here + a row in this table.
