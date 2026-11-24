# z2mqtt (zigbee2mqtt)

Zigbee2MQTT — bridges Zigbee devices to MQTT so Home Assistant can consume them. **19 devices** (2026-11-24: 9 SNZB-02P air sensors, 3 ZBMINIL2 light switches, SWV valve, SNZB-01P button, Aqara switch, Philips blinds switch, 2 Candeo routers).
**Versions (2026-11-24, z2m frontend → Settings → About; works without SSH):** z2m 2.14.2, herdsman 10.10.0. Coordinator now SLZB-MR5U radio 1, IEEE **`0xfc1119fffeaa036b`** (was SLZB-06M EmberZNet 8.0.2, IEEE `0x8c8b48fffe9583ba`).
**2026-11-10:** the 4 AVATTO TRVs, `Hall/Thermostat` (Shelly relay) and `Dining Room/Thermostat` (Bosch) were **removed** (replaced by
tado° X over Matter; see [../matter/README.md](../matter/README.md)). Backups: `/var/lib/zigbee2mqtt/{database.db,devices.yaml}.bak-pre-tado-20261110`.

**Force-remove ≠ gone (2026-11-10):** `force: true` only deletes z2m's record. A device that is still powered keeps the
network key and **rejoins** (3 of the AVATTO TRVs came back as bare `0xa4c…` at 07:10–19:23 the next day). Pull the batteries/power first, or remove
with `"block": true`. **z2m writes the block to `configuration.yaml`, which the NixOS module regenerates on every start**,
so a block must also go into `settings.blocklist` in `home-automation.nix` (done for those 3).

**Mesh has only 2 routers left (2026-11-10):** `Living Room/Lights` (C202) and `Loft Bedroom/Switch` (C-ZB-RD1P-DIM), plus the
coordinator. The tado swap took out 2 mains routers: the Shelly `Hall/Thermostat` and the Bosch `Dining Room/Thermostat`. All
the SONOFF ZBMINIL2 no-neutral light switches are **end devices**, so they need a router parent. `Entry Hall/Ligths` went silent
after 17:24 on 11-10, and later commands got `Delivery failed`. Fix: power-cycle it (breaker); a mains Zigbee router (smart plug) in the hall makes it durable.

**Removing a device without the frontend (verified 2026-11-10):** publish over MQTT as z2m's own user, reading the password
from `/var/lib/zigbee2mqtt/secret.yaml` on the box (never print it). `mosquitto_pub`/`_sub` are not on PATH: use
`/nix/store/*-mosquitto-2.*/bin/` (e.g. `ls -d /nix/store/*-mosquitto-2.1.2`). Request: topic
`zigbee2mqtt/bridge/request/device/remove`, payload `{"id":"<friendly name>","force":true}`. Use `force` for offline or sleepy battery
devices. Read the result on `zigbee2mqtt/bridge/response/device/remove`. z2m clears the device's retained `homeassistant/…/config`
topics, and HA drops the entities. **Gotcha:** a device that left the network on its own (e.g. a factory reset) is not in
`database.db`, so remove returns "does not exist", but its `devices.yaml` name and retained discovery topics remain. Clear those by
hand: publish an empty retained message (`-r -n`) to each `homeassistant/+/<ieee>/+/config`, stop z2m, delete the 2 lines from
`devices.yaml`, start z2m.

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
- **Coordinator = SLZB-MR5U radio 1 since 2026-11-24** (`tcp://192.168.11.121:6638`, EFR32MG24, ember fw 20250212, EZSP v13). Migrated
  from the SLZB-06M (`192.168.11.228`, EFR32MG21) by z2m backup restore. See "Coordinator migration" below. Radio 2 of the same box is the
  Thread OTBR ([../thread](../thread/README.md)), also on **channel 25**.
- **No local USB/serial device.** The Zigbee coordinator is **network-attached**: `serial.port: tcp://192.168.11.121:6638` (was `192.168.11.228` until 2026-11-24), `adapter: ember` (EZSP), baud 115200. So there is no `devices:` / `/dev/ttyUSB*` passthrough — the host `casaos` has no serial coordinator plugged in.
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

## Coordinator migration (SLZB-06M → SLZB-MR5U, 2026-11-24): runbook + gotchas
Worked without re-pairing. Steps as done:
1. `sudo systemctl stop zigbee2mqtt`. Stopping writes a fresh `coordinator_backup.json` (zigpy open-coordinator-backup; ember: keys, PAN, ext PAN,
   channel, `hashed_tclk`; `devices` is empty for ember, which is normal). Snapshot: `/var/lib/zigbee2mqtt.bak-pre-mr5u-20261124`, nix file
   `~/nixos/home-automation.nix.bak-pre-mr5u-20261124`.
2. Silence the old radio. An EZSP NCP **keeps running the network without a host**, so stopping z2m is not enough. SLZB-06M web UI → Settings →
   General → **Zigbee Flash Mode** (= `GET /api2?action=4&cmd=2`) puts the EFR32 in the Gecko bootloader. Verify with
   `(printf '\n'; sleep 3) | nc -w4 192.168.11.228 6638` → `Gecko Bootloader v1.A.3 … BL >`. **Not persistent:** SLZB-OS ≥3.3.1 reboots the
   radio on every SLZB boot, so a power blip brings the old coordinator back. **Unplug the SLZB-06M** (or reflash its radio) for good.
3. Change `serial.port` in `home-automation.nix` and deploy. z2m log: `Adapter network does not match config. Leaving network...` →
   `Forming from backup` → `New network formed!` → `zigbee-herdsman started (restored)`.
- **Coordinator IEEE did NOT carry over:** `Coordinator address changed, updating to '0xfc1119fffeaa036b'`. The MR5U radio already has a custom
  EUI64 burned in, and herdsman doesn't overwrite it. Same PAN/keys/channel, so devices stay joined. Reporting bindings made to the old IEEE
  may need **Reconfigure** in z2m (wake sleepy devices first) for any device that goes quiet.
- **`nixos-rebuild switch` restarts a manually stopped z2m** even when its config didn't change (that happened here on a failed edit: z2m
  briefly tried to talk to the bootloader. Harmless, but stop it again before continuing).
- `sed` with `#` as the delimiter fails on Nix comments. Use `perl -0pi -e 's|…|…|'`.
- Last-seen per device from the box: [`tools/lastseen.py`](tools/lastseen.py) (`database.db` `lastSeen`; only flushed periodically/on
  stop, so use MQTT traffic for "right now").
- **Frame-counter rollback after a coordinator reboot (hit 2026-11-24, ~20 min after the restore).** The MR5U was unplugged to move to PoE; on
  reboot the radio's NWK frame counter came back **lower** than before (backup 16:48 = 24 191 859 → 17:05 = 24 191 396). Routers (and devices
  that didn't rejoin) silently drop its frames as replays: `/get` → `Delivery failed for '<nwk>'`, network-map LQI scans fail, while end devices
  that **rejoined** (log `Accepting joining …`) work. Same physical spot, nothing RF-related; turning the MR5U's Thread off didn't change it.
  Check: `mosquitto_pub … -t zigbee2mqtt/bridge/request/backup -m '{}'` makes z2m rewrite `coordinator_backup.json`; compare
  `network_key.frame_counter` with the previous backup. Fix: generate traffic (repeated `/get`s) until the counter passes the old value; it also
  heals by itself with normal traffic. Avoid rebooting the coordinator in the first hours after a restore.
- **"Device published since restart" ≠ alive:** at startup z2m republishes every device's cached state (`cache_state_send_on_startup`), so all 20
  devices appear in the log within seconds. Count only publishes ≥ ~1 min after `zigbee-herdsman started`, or read with `/get` (mains devices).
- **Rollback:** stop z2m, MR5U Mode → radio 1 off/Router (or unplug), plug the SLZB-06M back (its radio still has the network), restore the
  `.bak-pre-mr5u` nix file + data dir, deploy. Do this soon: once the MR5U has run for a while, the old radio's NWK frame counter is
  behind and devices may drop its frames.
