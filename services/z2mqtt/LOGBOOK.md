# Logbook — z2mqtt

Reverse-chronological. Newest entry on top. One entry per task that touches **z2mqtt** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

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
