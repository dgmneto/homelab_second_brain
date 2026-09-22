# Logbook — homeassistant

Reverse-chronological. Newest entry on top. One entry per task that touches **homeassistant** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

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
