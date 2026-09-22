# Logbook — z2mqtt

Reverse-chronological. Newest entry on top. One entry per task that touches **z2mqtt** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-09-22 — Restarted to republish HA discovery
Broker had 0 `homeassistant/#` configs after a mosquitto restart; z2m healthy but didn't republish
(ignored manual `homeassistant/status online`). `docker restart z2mqtt` ×2 (once more after mosquitto
persistence change) → 253 configs. Noted file log stalled at 20:04 while MQTT kept flowing.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
