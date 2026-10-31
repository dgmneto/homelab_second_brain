# homeassistant

Home Assistant — central home-automation hub. Integrates Zigbee devices (via MQTT/zigbee2mqtt) and Matter devices (via matter-server).

> **Runs on homelab-notebook since 2026-10-31** (NixOS `services.home-assistant` 2026.10.4 from `nixpkgs-unstable`,
> config in `hosts/homelab-notebook/nixos/home-automation.nix`; whole stack + history in [MIGRATION.md](MIGRATION.md)).
> - UI `http://192.168.11.21:8123` / **`https://ha.intern.dgmneto.com`** (nginxIntern host 18 → `192.168.11.21:8123`).
> - Config dir **`/var/lib/hass`** (user `hass`, uid 286); `configuration.yaml` is the UI-managed one (Nix `config = null`).
>   Logs `journalctl -u home-assistant`. Restart: `sudo systemctl restart home-assistant` (~20 s; no LSIO permission pass).
> - **`http:` settings live in `.storage/http`, not YAML** (HA migrated them; YAML `trusted_proxies` is ignored). Trusted:
>   `192.168.11.13/32` (casaos host IP = nginxIntern NATed via the docker bridge), `192.168.14.34/32`, `172.21.0.83/32`.
> - `.storage/core.network` `configured_adapters = ["enp2s0"]` (don't let it pick `tailscale0`).
> - Broker `mosquitto` → `127.0.0.1` (`/etc/hosts`), Matter `ws://192.168.11.21:5580/ws`.
> - Python deps come from Nix: a new integration (even a discovery flow) can fail with `No module named …` until its domain
>   is in `extraComponents` (custom components: `extraPackages`). pip is skipped.
> - **No Watchtower any more**: the version is pinned by `flake.lock`. Upgrade = `nix flake update nixpkgs-unstable` + deploy.
> - Firewall: 8123, 21064 (HomeKit bridge), 1400 (Sonos callbacks)/tcp; 5353, 1900/udp.
> - Nightly backup of `/var/lib/hass` to casaos (`homelab-backup.timer`); HA's own backups land in `/var/lib/hass/backups`.
>   The pre-move `backups/` (283M) stayed in casaos `/footage/services/homeassistant/config/backups`.
>
> - **Dashboard all "Configuration error" = a custom card's JS isn't served.** The default dashboard is 13×
>   `custom:bubble-card`; resources (`.storage/lovelace_resources`) are `/hacsfiles/<repo>/<file>.js`, served by HACS from
>   `/var/lib/hass/www/community/<repo>/`. Check: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8123/hacsfiles/Bubble-Card/bubble-card.js`.
>   404 → files missing although HACS lists the repo as installed (`.storage/hacs.repositories` → `version_installed`).
>   Restore that exact version from the repo tag (Bubble-Card: `raw.githubusercontent.com/Clooos/Bubble-Card/<tag>/dist/bubble-card.js`;
>   there's no release asset) into that dir (owner `hass`, plus a `.js.gz`), or HACS → Redownload. No restart needed;
>   clients must reload/clear the frontend cache.
>
> - Known leftovers (sweep 2026-10-31): HACS lists **`better_thermostat` 1.7.0 installed but its code is gone and no config
>   entry uses it**; `tapo_control` code missing (entry + 109 entities exist). Automation **"Ground Floor/Update Thermostat
>   Temperature"** (off) targets the deleted `climate.ground_floor_thermostat_2`; the device now lives as
>   `climate.dining_room_thermostat` and the `ground_floor_new_trv_calibrator*` automations replaced it. The YAML `http:` block
>   is dead (Repairs: `http/yaml_still_present_after_migration`). Outbound IPv6 from the laptop fails fast (ULA only); harmless.
>   Boot-time-only noise: met.no DNS errors for ~3 min, template "invalid sensor state: unavailable", smlight once.
>
> Everything below describes the **old casaos container** (removed 2026-10-31; its config dir is kept for rollback/archive).

## Image
`lscr.io/linuxserver/homeassistant:latest` (LinuxServer.io build; **unpinned** — Watchtower updates it)

## Access
- Internal port: `8123/tcp`
- IPs: macvlan `192.168.14.73`, internal `172.21.0.173`, IPv6 net `192.168.15.73` / `fd00:2::73`
- Reverse-proxied via nginx-proxy-manager (`nginxProxyManagerProd` for external, `nginxIntern` for internal).

## Paths
- Compose: `/home/dgmneto/homelab/services/homeassistant/compose.yaml` (on `homelab`/casaos)
- Config: **`/footage/services/homeassistant/config`** → `/config` (bind mount)

## Networks / devices
- Runs `privileged: true`. No USB/serial passthrough (no `devices:` — Zigbee/Matter coordinators are reached over the network, not via local USB).
- Three external networks: `macVlanNetwork`, `internalNetwork`, `macVlanIPv6Network`.

## Integrations
- **Zigbee:** HA ← MQTT ← zigbee2mqtt. z2mqtt publishes to the `mosquitto` broker (`zigbee2mqtt` base topic) with HA discovery enabled; HA's MQTT integration subscribes.
- **Matter:** HA ← matter-server websocket at `ws://192.168.11.21:5580/ws` (homelab-notebook since 2026-10-30; was `192.168.15.25`). No Matter devices commissioned yet.
- Broker = `mosquitto` → since 2026-10-30 **homelab-notebook `192.168.11.21:1883`** via compose `extra_hosts` (MQTT entry still says `mosquitto`); anonymous disabled, auth required.
- **Recreating this container costs ~4 min:** the LinuxServer image re-fixes Python package permissions on a new container before HA starts.

## Quirks / runbook
- **`/footage` full → HA crash-loop.** HA's config is bind-mounted on the `/footage` LVM volume (`/footage/services/homeassistant/config`). When `/footage` fills to 100%, HA fails to write its SQLite recorder DB / config and crash-loops with `OSError: [Errno 28] No space left on device`, appearing "down" even though `/` has plenty of free space. **Check `df -h /footage` first.** Past recurring filler was the `openclaw` `chrome.service` crash-loop (see memory note) — `openclaw` was decommissioned 2026-08-03, so that specific cause no longer applies, but the "check `/footage` first" advice still holds for whatever fills it next.
- `autoheal` + `watchtower` containers run alongside; the `restart: always` policy plus autoheal will keep restarting HA, which masks the real disk-full cause.
- **"All devices missing" = MQTT entities `unavailable`, not a deleted registry.** 2026-09-22: a
  mosquitto restart (no persistence) wiped the retained z2m discovery configs; fixed by
  `docker restart z2mqtt` and enabling mosquitto persistence. Diagnose offline via
  `.storage/core.restore_state` (dumped every 15 min) joined to `.storage/core.entity_registry` by
  platform — no API token needed (script pattern in root LOGBOOK 2026-09-22).
- **Lost in the same incident (found 2026-10-31): `www/community/Bubble-Card`** (HACS plugin v3.1.6, every dashboard
  card). `www/community` was last modified 2026-09-22 21:19. Phones kept rendering from cache until the backend moved.
  Restored on homelab-notebook (see top).
- **`tapo_control` (HACS, JurajNyiri/HomeAssistant-Tapo-Control 7.1.13) folder is MISSING** from
  `/config/custom_components` (dir last changed 2026-08-10 23:13, just after the disk migration) while HACS
  still lists it installed and a config entry + 109 entities remain. No HA backup has it (only 3 kept, all
  ≥ Sep 20). Fix: HACS → Tapo Control → Redownload, then restart HA.
- **`octopus_energy` code is missing too** (found 2026-10-30): config entry present, no folder in
  `custom_components`. The NixOS move restores it from nixpkgs.
- **Migration to homelab-notebook in progress:** see [MIGRATION.md](MIGRATION.md).
- Image is unpinned (`latest`); a Watchtower pull can introduce breaking HA core upgrades.
