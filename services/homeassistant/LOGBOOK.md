# Logbook — homeassistant

Reverse-chronological. Newest entry on top. One entry per task that touches **homeassistant** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-30 — HA migration Phase 1 (mosquitto → homelab-notebook)
compose: `extra_hosts: mosquitto:192.168.11.21`, recreated 21:34. Down until 21:37:50 (LSIO "fixing python package permissions" pass on new containers), then connected to the laptop broker; no MQTT errors in the log.

## 2026-10-30 — Migration to homelab-notebook: Phase 0
See `MIGRATION.md`. Inventoried config entries (29 domains), custom components (hacs, espsomfy_rts,
zoned_heating on disk; **octopus_energy and tapo_control have entries but no code**), trusted_proxies
(needs nginxProd 192.168.14.33 added before moving), HomeKit bridge port 21064. Off-host copy of the
2026-10-30 automatic backup at `homelab-notebook:/var/backups/ha-migration/`. No change to the running HA.

## 2026-09-22 — "All devices missing": MQTT entities unavailable; tapo_control missing
188/188 mqtt entities unavailable (discovery wiped by mosquitto restart) → fixed via z2m restart +
mosquitto persistence; 21:13 restore_state dump shows 0 mqtt unavailable. Separately, HACS
`tapo_control` folder is gone from custom_components (since ~08-10); needs HACS redownload (user).

## 2026-09-22 — Investigation: reported down, found up
Container up 2d; 200 on `192.168.14.73:8123` and `https://ha.intern.dgmneto.com` from the LAN.
`external_url` = `ha.intern` (LAN-only; resolves publicly to a private IP), so HA cannot be reached
off-LAN. Logs: DNS timeouts to 192.168.11.1 ~01:00 09-22 (unifiprotect disconnect), otherwise quiet.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
