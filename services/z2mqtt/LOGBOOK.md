# Logbook — z2mqtt

Reverse-chronological. Newest entry on top. One entry per task that touches **z2mqtt** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-26 — Switches not responding: stale old-coordinator binds removed (in progress)
User: kitchen, hall and loft bedroom switches misbehave. Found: 13× Kitchen/Switch + 12× Entry Hall set failures today (`Delivery failed`), 1 Loft
Bedroom/Switch brightness failure; `BROADCAST failed '65533'` ramping from 11-25 23:00 (~280/h overnight); NCP counters: APS unicast 34 ok / 775 failed,
CCA fails ≈ 0, MR5U uptime 44 h (no reboot → not a frame-counter rollback). `database.db`: **every** device still bound to the old IEEE
(configure never unbinds). Backed up `database.db.bak-pre-unbind-20261126`, installed external extension `cleanup-old-coordinator-binds.js`
(see README). Removed at once: Living Room/Lights, Office/Lights, Little Room/Lights, Guest Room/Lights, Loft Bedroom/Switch (all 4 clusters).
After that both routers answer `/get`. Broadcast failures had already fallen to ~0 from 12:40. Still stale (14, sleepy or unreachable): Kitchen/Switch,
Entry Hall/Ligths, Loft bedroom button, Garden/Water, Loft Bedroom/Blinds Switch, 9 air sensors; they clean up as they wake. Network map: Kitchen/Switch
child of Living Room/Lights, downlink fails (one-way); Entry Hall has no parent. Both need a breaker power-cycle on site.

## 2026-11-24 — Re-bind status at 18:56 (open)
Retry loops 17:56–18:56 re-bound Office + Little Room air sensors (7/19 total on the new IEEE). **Still bound to the old IEEE, so not reporting:**
Kitchen/Switch, Entry Hall/Ligths, Garden/Water, Loft Bedroom/Blinds Switch, Loft bedroom button, Kitchen, Living Room, Dining Room, Guest Bathroom,
Guest Bedroom, Loft Bathroom and Loft Bedroom air sensors. Needs: press each device's button (Entry Hall: breaker) while `device/configure` is retried.

## 2026-11-24 — Sensors silent: bindings still on old coordinator IEEE → reconfigure
9 air sensors, button, blinds switch, Entry Hall silent since 16:54 (normally 4–14 reports/26 min). `database.db`: all binds →
`0x8c8b48fffe9583ba` (old IEEE). `device/configure` for all 19: OK for Living Room/Lights, Loft Bedroom/Switch, Office/Lights, Little Room/Lights,
Guest Room/Lights; 14 sleepy/unreachable failed (`Delivery failed`). Started a 45-min retry loop; the user was asked to press each sensor's button.

## 2026-11-24 — SLZB-06M unplugged
User unplugged the old coordinator (radio not reset; kept as rollback). Verified offline from the Mac (`nc -z 192.168.11.228 80` fails).

## 2026-11-24 — MR5U moved to PoE → frame-counter rollback, fixed
Graceful move (z2m stopped, MR5U Thread disabled, then re-enabled → z2m "started (resumed)"). After it, both routers (`Living Room/Lights` nwk 10001,
`Loft Bedroom/Switch` 52280) and `Entry Hall/Ligths` failed every `/get` with `Delivery failed`. Same physical spot; disabling MR5U Thread didn't help.
Forced backup showed NWK frame counter 24 191 396 < 24 191 859 from before the reboot. Ran repeated `/get`s to 6 mains devices (29 rounds, ~2 min):
both routers answered from 17:07. Network map 17:08: 17/19 devices in neighbour tables; not yet seen: Dining Room + Guest Bedroom air sensors,
Entry Hall/Ligths (historically needs a breaker power-cycle).

## 2026-11-24 — Coordinator migrated SLZB-06M → SLZB-MR5U radio 1 (backup restore)
`systemctl stop zigbee2mqtt` (wrote fresh coordinator_backup.json 16:32), snapshot `/var/lib/zigbee2mqtt.bak-pre-mr5u-20261124`. SLZB-06M radio put
in Zigbee Flash Mode (bootloader; verified `Gecko Bootloader v1.A.3` on :6638). `serial.port` → `tcp://192.168.11.121:6638`, deployed. z2m:
"Forming from backup" → "New network formed!" → "started (restored)", 20 devices. **Coordinator IEEE changed** 0x8c8b48fffe9583ba →
0xfc1119fffeaa036b (MR5U EUI64 not rewritable). Verified: both routers answer `/get`; within ~15 min 15 of 19 devices sent live reports
(sensors, switches, blinds, button); 5 sleepy devices pending at commit time. A failed sed edit + rebuild restarted z2m against the
bootloader for a few seconds (no harm). User told to unplug the SLZB-06M and keep it un-reset for rollback.

## 2026-11-24 — Investigation: coordinator migration to SLZB-MR5U (planning only)
Read-only. z2m 2.14.2 / herdsman 10.10.0 / EmberZNet 8.0.2, coordinator IEEE 0x8c8b48fffe9583ba, 19 devices. Target: MR5U radio 1 EFR32MG24 ember fw 20250212. Migration plan proposed (backup → stop z2m → old adapter off → repoint serial.port → restore on start); nothing changed. SSH was blocked by 1Password, data read from the z2m frontend.

## 2026-11-10 — Rejoined TRVs blocked; Entry Hall switch lost its parent
3 force-removed AVATTO TRVs (batteries still in) rejoined 07:10–19:23 as `0xa4c…`. Removed again with `block: true`;
blocklist also added to the Nix z2m settings (the module regenerates configuration.yaml) and deployed, verified present after
restart. `Entry Hall/Ligths` (ZBMINIL2, end device) last seen 17:24, `Delivery failed` at 20:49. The mesh is down to 2 routers after
the Shelly/Bosch removal (both physically gone since 11-09). Needs a power-cycle on site.

## 2026-11-10 — Removed the 6 heating devices replaced by tado° X
Via MQTT `bridge/request/device/remove` (force) as the zigbee2mqtt user: Little Room, Guest Bedroom and Loft Bedroom TRV
Valves, Hall/Thermostat, Dining Room/Thermostat → all `ok`. Office/TRV Valve "does not exist" (had already left the network),
so its 19 retained discovery topics were cleared by hand and its devices.yaml entry deleted (z2m stopped/started). Backups
`database.db`/`devices.yaml` `.bak-pre-tado-20261110`. z2m active, no errors after restart.

## 2026-11-10 — Identified heating devices replaced by tado° X
Read-only. 4 AVATTO TRVs still online; Shelly `Hall/Thermostat` last seen 11-09 17:47, Bosch `Dining Room/Thermostat` last
seen 11-09 15:00. HA's Ground Floor calibrator makes z2m log a failed publish to the Bosch every 5 min. No change made.

## 2026-10-30 — HA migration Phase 2
Moved to homelab-notebook (NixOS). casaos container removed 21:53:30; data split into devices/groups/secret.yaml; network resumed on the laptop at ~21:56 with all 26 devices. pan_id/ext_pan_id must be literals (no `!secret` support). UI proxy (nginxIntern host 21) repointed.

## 2026-10-30 — HA migration Phase 1 (mosquitto → homelab-notebook)
compose: `extra_hosts: mosquitto:192.168.11.21`, recreated 21:33:48. Reconnected to the laptop broker within ~10 s; `bridge/state` online, health_check healthy.

## 2026-09-22 — Restarted to republish HA discovery
Broker had 0 `homeassistant/#` configs after a mosquitto restart; z2m healthy but didn't republish
(ignored manual `homeassistant/status online`). `docker restart z2mqtt` ×2 (once more after mosquitto
persistence change) → 253 configs. Noted file log stalled at 20:04 while MQTT kept flowing.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
