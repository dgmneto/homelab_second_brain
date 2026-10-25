# Logbook — nginxIntern

Reverse-chronological. Newest entry on top. One entry per task that touches **nginxIntern** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

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
