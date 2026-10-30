# Logbook — matter

Reverse-chronological. Newest entry on top. One entry per task that touches **matter** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-30 — Container name fix; migration Phase 0
The container is `matter-server`, not `matter` (`docker inspect matter` fails); README corrected.
Version 8.1.2, same as nixpkgs. Data dir holds the fabric JSON + chip*.ini + credentials/ (1.3M).
Migration plan: `../homeassistant/MIGRATION.md` (Phase 3). No change to the running service.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
