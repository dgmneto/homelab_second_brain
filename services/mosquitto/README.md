# mosquitto

Eclipse Mosquitto — the MQTT broker for the homelab. Central message bus: zigbee2mqtt publishes, Home Assistant subscribes.

> **Moved 2026-10-30 to homelab-notebook** (NixOS `services.mosquitto`, `hosts/homelab-notebook/nixos/home-automation.nix`):
> `192.168.11.21:1883`, users `zigbee2mqtt`/`homeassistant`/`dgmneto` (hashes in root-only
> `/etc/mosquitto-secrets/<user>.hash`, never in the repo), `readwrite #` ACL each, persistence in
> `/var/lib/mosquitto/mosquitto.db`, logs `journalctl -u mosquitto`. casaos clients reach it as `mosquitto` via
> compose `extra_hosts`. The casaos container below still runs **idle, for rollback only** (Phase 5 removes it).
> Runbook: [MIGRATION.md](../homeassistant/MIGRATION.md). The rest of this file describes the casaos container.

## Image
`eclipse-mosquitto:latest` (**unpinned**)

## Access
- Listener: `1883/tcp` (plain MQTT)
- IPs: macvlan `192.168.14.82`, internal `172.21.0.182`
- Clients reach it as host `mosquitto` (Docker DNS) → `192.168.14.82:1883`.

## Paths
- Compose: `/home/dgmneto/homelab/services/mosquitto/compose.yaml`
- Config: `/footage/services/mosquitto/config` → `/mosquitto/config`
- Data: `/footage/services/mosquitto/data` → `/mosquitto/data`
- Log: `/footage/services/mosquitto/log` → `/mosquitto/log`

## Config (mosquitto.conf)
```
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwd
persistence true                       # added 2026-09-22 — see below
persistence_location /mosquitto/data/
autosave_interval 300
```
Pre-change copy: `/mosquitto/config/mosquitto.conf.bak-20260922`. The config dir is owned by uid 1883;
`dgmneto` can't write it without sudo — edit via `docker exec -u root mosquitto sh -c '...'` instead.
- **Auth required** — anonymous disabled. Credentials live in `/mosquitto/config/passwd` (hashed; never copy out). Users include `zigbee2mqtt` and the HA MQTT user.

## Networks / devices
- Networks: `macVlanNetwork`, `internalNetwork`. No devices.

## Integrations
- This IS the broker. zigbee2mqtt → publishes (user `zigbee2mqtt`). Home Assistant → subscribes via its MQTT integration. Topic flow: z2mqtt → mosquitto → HA.

## Quirks / runbook
- **Before 2026-09-22 there was no `persistence`**, so every broker restart (watchtower pulls
  `latest`) wiped all *retained* messages, including the ~253 `homeassistant/#` discovery configs from
  zigbee2mqtt → **every Zigbee entity in HA went `unavailable`** ("all devices missing"). Persistence is
  now on; if it recurs, count discovery configs:
  `docker exec mosquitto mosquitto_sub -u zigbee2mqtt -P <pw> -t 'homeassistant/#' -W 5 | wc -l`
  (pw = `mqtt.password` in `/footage/services/z2mqtt/data/configuration.yaml`, read into a shell var,
  never print it). **Don't grep/sed it out**: that yields a wrong value (YAML quoting) → "not authorised". Use z2m's parser:
  `PW=$(sudo docker exec -w /app z2mqtt node -e 'const y=require("js-yaml");process.stdout.write(String(y.load(require("fs").readFileSync("/app/data/configuration.yaml","utf8")).mqtt.password))')`.
  Since Phase 1 query the laptop broker with `-h 192.168.11.21` (265 configs on 2026-10-30). `0` → `docker restart z2mqtt` republishes them. Note: publishing
  `homeassistant/status online` by hand did **not** make z2m republish (waited 15s).
- Single plain `1883` listener, no TLS — fine because traffic stays on the LAN/macvlan.
- To add an MQTT user: `docker exec -it mosquitto mosquitto_passwd /mosquitto/config/passwd <user>` then restart. Do not commit the `passwd` file.
- Config/data/log all on `/footage`; a full volume can stop the broker from persisting and break all MQTT-dependent automations.
- Unpinned `latest`.
