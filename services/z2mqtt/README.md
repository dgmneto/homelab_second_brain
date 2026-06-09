# z2mqtt (zigbee2mqtt)

Zigbee2MQTT — bridges Zigbee devices to MQTT so Home Assistant can consume them. ~25 devices (lights, TRV valves, air sensors, switches, thermostats, blinds).

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
- **MQTT:** connects to broker at `mqtt://mosquitto:1883` (resolves to `192.168.14.82`) as user `zigbee2mqtt`, base topic `zigbee2mqtt`, `retain: true`. Password is in `configuration.yaml` (not reproduced here).
- **HA:** `homeassistant.enabled: true` → publishes HA MQTT-discovery messages. Flow: HA ← MQTT (mosquitto) ← z2mqtt.

## Quirks / runbook
- Coordinator is over the LAN/TCP — if `192.168.11.228:6638` is unreachable, z2mqtt logs serial/connection errors and Zigbee goes dark even though the container is "Up". Check that host first, not a USB stick.
- Data lives on `/footage`; a full `/footage` can break z2mqtt persistence/logging too.
- Unpinned `latest` image; z2mqtt config schema occasionally changes between majors — a Watchtower bump can break the config.
