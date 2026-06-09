# mosquitto

Eclipse Mosquitto — the MQTT broker for the homelab. Central message bus: zigbee2mqtt publishes, Home Assistant subscribes.

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
```
- **Auth required** — anonymous disabled. Credentials live in `/mosquitto/config/passwd` (hashed; never copy out). Users include `zigbee2mqtt` and the HA MQTT user.

## Networks / devices
- Networks: `macVlanNetwork`, `internalNetwork`. No devices.

## Integrations
- This IS the broker. zigbee2mqtt → publishes (user `zigbee2mqtt`). Home Assistant → subscribes via its MQTT integration. Topic flow: z2mqtt → mosquitto → HA.

## Quirks / runbook
- Single plain `1883` listener, no TLS — fine because traffic stays on the LAN/macvlan.
- To add an MQTT user: `docker exec -it mosquitto mosquitto_passwd /mosquitto/config/passwd <user>` then restart. Do not commit the `passwd` file.
- Config/data/log all on `/footage`; a full volume can stop the broker from persisting and break all MQTT-dependent automations.
- Unpinned `latest`.
