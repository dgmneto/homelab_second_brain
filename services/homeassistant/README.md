# homeassistant

Home Assistant — central home-automation hub. Integrates Zigbee devices (via MQTT/zigbee2mqtt) and Matter devices (via matter-server).

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
- **Matter:** HA ← matter-server websocket at `ws://192.168.15.25:5580/ws` (matter-server `stable`).
- Broker = `mosquitto` (`192.168.14.82:1883`, anonymous disabled — auth required).

## Quirks / runbook
- **`/footage` full → HA crash-loop.** HA's config is bind-mounted on the `/footage` LVM volume (`/footage/services/homeassistant/config`). When `/footage` fills to 100%, HA fails to write its SQLite recorder DB / config and crash-loops with `OSError: [Errno 28] No space left on device`, appearing "down" even though `/` has plenty of free space. **Check `df -h /footage` first.** Past recurring filler was the `openclaw` `chrome.service` crash-loop (see memory note) — `openclaw` was decommissioned 2026-08-03, so that specific cause no longer applies, but the "check `/footage` first" advice still holds for whatever fills it next.
- `autoheal` + `watchtower` containers run alongside; the `restart: always` policy plus autoheal will keep restarting HA, which masks the real disk-full cause.
- Image is unpinned (`latest`); a Watchtower pull can introduce breaking HA core upgrades.
