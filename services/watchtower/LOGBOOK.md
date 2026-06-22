# Logbook — watchtower

Reverse-chronological. Newest entry on top. One entry per task that touches **watchtower** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-22 — Switch from 30s interval to weekly cron
Investigated hermes gateway restarting constantly. Root cause: `nousresearch/hermes-agent:latest`
was being published 30+ times/day by upstream; watchtower's `--interval 30` picked up each new
image immediately, restarting the container each time (26 restarts on 2026-06-21 alone).
Changed `--interval 30` to `--schedule "0 0 10 * * 0"` (Sundays 10:00 UTC) for all containers.
Applied on server: `docker compose up -d` in `/home/dgmneto/homelab/services/watchtower/`.
Verified: `docker logs watchtower` shows "Scheduling first run: 2026-06-28 10:00:00 +0000 UTC".

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
