# Logbook — mosquitto

Reverse-chronological. Newest entry on top. One entry per task that touches **mosquitto** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-09-22 — Enabled persistence (retained discovery was wiped on restart)
09-20 watchtower restart (→ 2.1.2) dropped all retained msgs incl. HA discovery → all Zigbee entities
unavailable in HA. Appended `persistence true` / `persistence_location /mosquitto/data/` /
`autosave_interval 300` via `docker exec -u root`; backup `mosquitto.conf.bak-20260922`;
`docker restart mosquitto` + `docker restart z2mqtt`; 253 `homeassistant/#` retained configs verified.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
