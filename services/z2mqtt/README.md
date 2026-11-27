# z2mqtt (zigbee2mqtt)

Zigbee2MQTT — bridges Zigbee devices to MQTT so Home Assistant can consume them. **19 devices** (2026-11-24: 9 SNZB-02P air sensors, 3 ZBMINIL2 light switches, SWV valve, SNZB-01P button, Aqara switch, Philips blinds switch, 2 Candeo routers).
**Versions (2026-11-24, z2m frontend → Settings → About; works without SSH):** z2m 2.14.2, herdsman 10.10.0. Coordinator = SLZB-MR5U radio 1 (EmberZNet 7.4.2, EZSP 13).
**Coordinator IEEE is `0x8c8b48fffe9583ba` again since 2026-11-27.** That is the old SLZB-06M's IEEE, restored on the MR5U through the NVM3
`STACK_RESTORED_EUI64` token. The MR5U's own burned-in EUI64 is `0xfc1119fffeaa036b`, used 11-24→11-27. See "Coordinator IEEE restore" below.
**⚠ The unplugged SLZB-06M still holds this network and the same IEEE. Never plug it back in without erasing its radio first.**
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
   radio on every SLZB boot, so a power blip brings the old coordinator back. **Unplug the SLZB-06M** (or reflash its radio) for good. **Done 2026-11-24 ~17:20: SLZB-06M unplugged, radio NOT reset** (still holds the old network = rollback path for a few days; HA's `smlight` entry for it will show unavailable).
3. Change `serial.port` in `home-automation.nix` and deploy. z2m log: `Adapter network does not match config. Leaving network...` →
   `Forming from backup` → `New network formed!` → `zigbee-herdsman started (restored)`.
- **Coordinator IEEE did NOT carry over** (superseded 2026-11-27: **restore the old IEEE instead**, see the next section; the reconfigure approach below deadlocked): `Coordinator address changed, updating to '0xfc1119fffeaa036b'`. The MR5U radio already has a custom
  EUI64 burned in, and herdsman doesn't overwrite it. Same PAN/keys/channel, so devices stay joined, **but every reporting binding still targets
  the old IEEE `0x8c8b48fffe9583ba`** (`database.db` → `endpoints.*.binds[].deviceIeeeAddress`). It kept working for ~20 min while devices had the
  old IEEE→0x0000 mapping cached. After the PoE-reboot outage they lost it, and **all battery sensors went silent** (0 reports in 50 min vs
  4–14 per 26 min normally). **Fix = reconfigure every device** (`zigbee2mqtt/bridge/request/device/configure` `{"id":"<name>"}`) right after a
  migration, before anything else happens. Routers and rx-on switches re-bind at once. Sleepy devices fail with `Delivery failed`
  until woken (press their button; retry configure in a loop). **Next migration: reconfigure all devices immediately after the restore.**
- **…and then remove the OLD binds: configure adds the new bind but never removes the old one** _(2026-11-27: this approach stalled at 11 devices. The real fix was restoring the old IEEE; see "Coordinator IEEE restore". The extension in `tools/` now has OLD/NEW swapped.)_ (found 2026-11-26: all 19
  devices still had binds to `0x8c8b48fffe9583ba`, even the re-bound ones). Devices keep trying to resolve that
  dead IEEE, which showed up as `Delivery of BROADCAST failed for '65533'` (up to ~300/h, from 11-25 23:00) and
  APS unicast failures (NCP COUNTERS idx 11 `APS_DATA_TX_UNICAST_FAILED` 775 vs idx 9 success 34 per period, while MAC tx was
  fine and idx 32 `PHY_CCA_FAIL` ≈ 0, so not RF/channel). Commands to Kitchen/Switch, Entry Hall and Loft Bedroom/Switch timed out.
  `bridge/request/device/unbind` can't target an IEEE that isn't a device, so the fix is the external extension
  [`tools/cleanup-old-coordinator-binds.js`](tools/cleanup-old-coordinator-binds.js) (installed 2026-11-26 via
  `bridge/request/extension/save`; lives in `/var/lib/zigbee2mqtt/external_extensions/`, survives restarts). It sends a ZDO Unbind for every old-IEEE
  bind (routers at once, sleepy devices when they next talk), drops it from `database.db`, and clears `meta.configured` on devices with
  no new bind so z2m's Configure re-binds them on their next message. Progress: `journalctl -u zigbee2mqtt | grep old-binds`.
  **Remove it once it logs `[old-binds] all clean`:** `bridge/request/extension/remove {"name":"cleanup-old-coordinator-binds.js"}`.
  List stale binds offline: see the 2026-11-26 LOGBOOK entry (python over `database.db`, `endpoints.*.binds[].deviceIeeeAddress`).
- **Decode `[NCP COUNTERS]`:** the index order is `EmberCounterType` in herdsman `dist/adapter/ember/enums.js` (0 MAC_RX_BROADCAST … 11
  APS_DATA_TX_UNICAST_FAILED, 12 ROUTE_DISCOVERY_INITIATED, 21 NWK_FRAME_COUNTER_FAILURE, 32 PHY_CCA_FAIL_COUNT, 33 BROADCAST_TABLE_FULL).
- **MQTT from the box (verified 2026-11-26):** `nix shell nixpkgs#mosquitto -c mosquitto_pub -h 127.0.0.1 -u zigbee2mqtt -P "$PW" …` with
  `PW=$(sudo grep mqtt_password /var/lib/zigbee2mqtt/secret.yaml | sed -E "s/^[^:]*: *//; s/^['\"]//; s/['\"]$//")`. Device state topics are **not
  retained** (a `mosquitto_sub -C 1` on `zigbee2mqtt/<dev>` waits for the next report). Network map: `bridge/request/networkmap`
  `{"type":"raw","routes":false}` → `bridge/response/networkmap` (~2.5 min; `links[]` = target's neighbour table, relationship 0 parent / 1 child / 2 sibling).
- **Kitchen/Switch (Aqara `lumi.switch.acn058`, no-neutral end device) one-way since 11-25:** _(2026-11-27: fixed without a power-cycle by restoring the old coordinator IEEE. The Aqara's downlinks work behind the Candeo router again, so the "Aqara behind third-party router" theory was wrong.)_ reports arrive, but every downlink fails
  `Delivery failed for '11909'`. Its parent is now the Candeo router `Living Room/Lights` (LQI 151); before the migration it presumably sat
  on the coordinator. Aqara end devices are known to misbehave behind third-party routers. Fix = power-cycle it at the breaker so it
  rejoins (ideally onto the coordinator). `Entry Hall/Ligths` has **no parent in the network map at all** (orphaned again; breaker power-cycle).

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
  **Obsolete since 2026-11-27:** the MR5U now carries the old IEEE, so the SLZB-06M is a clone. Erase its radio before any reuse.

## Coordinator IEEE restore (2026-11-27): the real fix for a migration to an ember adapter with a different EUI64
**Symptom (11-24 → 11-27):** 6 SNZB-02P sensors sent nothing for 2+ days. Commands to devices parented by a router failed (`Delivery failed`):
`Kitchen/Switch` (Aqara) wouldn't switch, and `/get` timed out. The log showed a constant stream of `zh:ember: Delivery of BROADCAST failed for '65533'`.
**Cause:** every pre-migration binding and each device's stored TC address pointed at `0x8c8b48fffe9583ba`. Devices kept broadcasting
`NWK_addr_req` for that IEEE (in debug: `ezspMessageSentHandler type=BROADCAST … clusterId 0 … messageTag=255` = relayed broadcasts from the
devices), and nobody answered. That filled the broadcast tables and starved the two Candeo routers. Re-binding per device
(`device/configure`, or the `cleanup-old-coordinator-binds.js` extension from 11-26) **deadlocked**: the silent sensors never send, so
they never "wake", and ZDO bind/unbind to router children failed anyway. Only devices whose parent was the coordinator got fixed.
**Fix (verified):** give the MR5U the old IEEE through the NVM3 token `STACK_RESTORED_EUI64` (key `0x1e12a`, little-endian bytes). It's writable on
EFR32MG2x/EZSP ≥13 even though the MFG `CUSTOM_EUI_64` is already burned:
1. Snapshot: `bridge/request/backup` + `sudo cp -a /var/lib/zigbee2mqtt /var/lib/zigbee2mqtt.bak-pre-eui64-20261127`.
2. Load [`tools/eui64-probe.js`](tools/eui64-probe.js) (read-only; logs current EUI64 + token, blank = `ffffffffffffffff`), then
   [`tools/set-eui64.js`](tools/set-eui64.js) via `bridge/request/extension/save` (`{"name":…,"code":…}`, see [`tools/zq.sh`](tools/zq.sh)).
   Both run on extension load, inside the adapter queue (`zigbee.zhController.adapter.ezsp`).
3. **Remove both extensions and any bind-cleanup extension whose OLD/NEW are about to flip**, then `systemctl restart zigbee2mqtt`. The ASH
   reset reboots the NCP. Log: `Coordinator address changed, updating to '0x8c8b48fffe9583ba'` → `started (resumed)`.
4. Within 1–4 min all silent sensors reported again, and Kitchen/Switch + Garden/Water answered `/get`.
5. Devices that had been re-bound to `0xfc11…` in the meantime (both routers, 3 ZBMINIL2s, Office/Little Room/Guest Bedroom sensors) need
   `device/configure` and removal of the `0xfc11…` binds. [`tools/cleanup-old-coordinator-binds.js`](tools/cleanup-old-coordinator-binds.js)
   (OLD/NEW swapped) is loaded for that. Remove it once it logs `[old-binds] all clean`.
**Revert:** same extension with `DATA = "ffffffffffffffff"` + restart → MR5U falls back to its own `0xfc1119fffeaa036b`.
**Next migration:** do this right after the restore, before anything else, if the new adapter's IEEE differs.
**Helpers** (box has no python3/jq on PATH; use `/nix/store/*-python3-3.12*/bin/python3`): [`tools/zq.sh`](tools/zq.sh) publishes as the z2m
MQTT user (`sudo sh zq.sh <topic-suffix> '<json>'`; reads the password from `secret.yaml`, never prints it). [`tools/nm.py`](tools/nm.py) = parent/child links from
the latest network map in the journal. [`tools/fails.py`](tools/fails.py) = failed set/get per hour and device. Temporary debug logging:
`bridge/request/options {"options":{"advanced":{"log_level":"debug"}}}` (set back to `info` afterwards; not persisted across the Nix-regenerated config).
**Not related:** `Loft Bedroom/Switch` (Candeo dimmer) publishes about 0.2 msg/s (electrical-measurement reports). It's noisy but harmless.
