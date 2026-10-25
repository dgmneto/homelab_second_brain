# Logbook — terminus

Reverse-chronological. Newest entry on top. One entry per task that touches **terminus** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-25 — Deploy Terminus (TRMNL BYOS) 0.78.0
New stack at `~/homelab/services/terminus` (web, sidekiq worker, postgres 18.6, valkey 9.1), data under
`/footage/services/terminus`, port 2300 on host, DB/valkey not published, watchtower disabled for
the stack. Secrets generated into new 1Password item `Homelab/Terminus`, `.env` rendered via
`op inject` (600). `docker compose up -d`: migrations ran, all containers healthy; from Mac
`http://192.168.11.13:2300/` → 302 /login. Committed to server repo (9c6de41). Device not yet
pointed at it; no admin registered yet; no NPM hostname.
