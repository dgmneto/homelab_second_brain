# Logbook — nginxIntern

Reverse-chronological. Newest entry on top. One entry per task that touches **nginxIntern** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-31 — HA migration Phase 4 (Home Assistant → homelab-notebook)
Proxy host 18 (`ha.intern.dgmneto.com`) forward_host `homeassistant` → `192.168.11.21` (HA moved to homelab-notebook). DB via knex + `18.conf`, reload; 200 once HA trusted 192.168.11.13. DB copy `database.sqlite.bak-pre-ha-move`.

## 2026-10-30 — HA migration Phase 2
Proxy host 21 (`z2m.intern.dgmneto.com`) forward_host 192.168.14.96 → 192.168.11.21 (z2m moved to homelab-notebook). Edited the DB via knex in the container + `21.conf`, `nginx -t` OK, reloaded; 200 via proxy. Recipe added to README.

## 2026-10-25 — Removed terminus /api/setup/ shim
Proxy host 25 advanced config emptied: the exact `location = /api/setup/` made nginx 301 `/api/setup`
(no slash), breaking TRMNL firmware 1.8.17. Verified `/api/setup` reaches Terminus afterwards.

## 2026-10-25 — Proxy host 25 (terminus) advanced config
Added exact `location = /api/setup/` → upstream `/api/setup` for old TRMNL firmware. Learned:
`rewrite` is ignored because NPM's proxy.conf forwards `$request_uri`. Documented in README.

## 2026-10-25 — Proxy host terminus.intern.dgmneto.com (id 25)
Created via REST API (recipe in README) → `terminus:2300`, cert 1, ssl forced. Verified 302 → /login from Mac.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
