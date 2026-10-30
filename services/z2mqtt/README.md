# z2mqtt (zigbee2mqtt)

Zigbee2MQTT — bridges Zigbee devices to MQTT so Home Assistant can consume them. 26 devices (lights, TRV valves, air sensors, switches, thermostats, blinds).

> **Moved 2026-10-30 to homelab-notebook** (NixOS `services.zigbee2mqtt`, `hosts/homelab-notebook/nixos/home-automation.nix`).
> Data `/var/lib/zigbee2mqtt` (uid 317): `configuration.yaml` is **regenerated from Nix on every start**, so
> change settings in the Nix file. Devices/groups live in `devices.yaml`/`groups.yaml` (z2m edits these), and
> `mqtt_password` + `network_key` in root-readable-only `secret.yaml` (never in the repo). Logs: `journalctl -u zigbee2mqtt`
> (JSON) + `/var/lib/zigbee2mqtt/log/`. UI `http://192.168.11.21:8080` / `https://z2m.intern.dgmneto.com`.
> Health check from the laptop: `mosquitto_sub/pub -h 127.0.0.1 -u zigbee2mqtt -P <mqtt_password from secret.yaml>`.
> casaos container **removed**; `/footage/services/z2mqtt/data` kept as of the cutover. Below = the old casaos setup.

## Image
`ghcr.io/koenkk/zigbee2mqtt:latest` (**unpinned**)

## Access
- Frontend: `8080/tcp` (enabled in config)
- IPs: macvlan `192.168.14.96`, internal `172.21.0.196`
- Reach the UI via nginx-proxy-manager (`nginxIntern`).

## Paths
- Compose: `/home/dgmneto/homelab/services/z2mqtt/compose.yaml`
- Config/data: `/footage/services/z2mqtt/data` → `/app/data` (incl. `configuration.yaml`)

## Networks / devices
- Networks: `macVlanNetwork`, `internalNetwork`.
- **No local USB/serial device.** The Zigbee coordinator is **network-attached**: `serial.port: tcp://192.168.11.228:6638`, `adapter: ember` (EZSP), baud 115200. So there is no `devices:` / `/dev/ttyUSB*` passthrough — the host `casaos` has no serial coordinator plugged in.
- Zigbee network: channel 25, pan_id 62.

## Integrations
- **MQTT:** connects to broker at `mqtt://mosquitto:1883` (since 2026-10-30 resolves to **homelab-notebook `192.168.11.21`** via compose `extra_hosts`; was `192.168.14.82`) as user `zigbee2mqtt`, base topic `zigbee2mqtt`, `retain: true`. Password is in `configuration.yaml` (not reproduced here).
- **HA:** `homeassistant.enabled: true` → publishes HA MQTT-discovery messages. Flow: HA ← MQTT (mosquitto) ← z2mqtt.

## Quirks / runbook
- **HA shows every Zigbee device unavailable but z2m is fine** → HA discovery configs missing from the
  broker (see `../mosquitto/README.md`). Fix: `docker restart z2mqtt` (republishes 253 configs on start).
- `docker logs z2mqtt` is empty for long stretches; the real log is
  `/app/data/log/<start-timestamp>/log.log` inside the container (rotates at 10MB, keeps 3). It can stop
  being written while z2m keeps working (seen 2026-09-22) — check MQTT traffic, not the file, for liveness:
  publish `{}` to `zigbee2mqtt/bridge/request/health_check`, expect `bridge/response/health_check`.
- Coordinator is over the LAN/TCP — if `192.168.11.228:6638` is unreachable, z2mqtt logs serial/connection errors and Zigbee goes dark even though the container is "Up". Check that host first, not a USB stick.
- Data lives on `/footage`; a full `/footage` can break z2mqtt persistence/logging too.
- Unpinned `latest` image; z2mqtt config schema occasionally changes between majors — a Watchtower bump can break the config.
