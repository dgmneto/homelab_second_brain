# Logbook — terminus

Reverse-chronological. Newest entry on top. One entry per task that touches **terminus** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-25 — Own IPs: macvlan 192.168.14.40 + internalNetwork 172.21.0.140
Added `macVlanNetwork` (192.168.14.40) and pinned `internalNetwork` (172.21.0.140) on the web
container; host port 2300 kept. IPs chosen after checking `docker network inspect` + compose files
and ping/arp from the Mac. `docker compose up -d web` → healthy. From Mac: 192.168.14.40:2300,
192.168.11.13:2300 and https://terminus.intern.dgmneto.com all → 302 /login. API_URI unchanged
(device stays paired). Server repo commit pushed.

## 2026-10-25 — Add terminus.intern.dgmneto.com
nginxIntern proxy host id 25 created via NPM REST API (creds from `op://Homelab/nginx` piped, not
printed): `terminus:2300`, cert 1, SSL forced, websockets on. Verified from Mac:
`https://terminus.intern.dgmneto.com/` → 302 `/login`, TLS verify OK. API_URI left on LAN IP.

## 2026-10-25 — Deploy Terminus (TRMNL BYOS) 0.78.0
New stack at `~/homelab/services/terminus` (web, sidekiq worker, postgres 18.6, valkey 9.1), data under
`/footage/services/terminus`, port 2300 on host, DB/valkey not published, watchtower disabled for
the stack. Secrets generated into new 1Password item `Homelab/Terminus`, `.env` rendered via
`op inject` (600). `docker compose up -d`: migrations ran, all containers healthy; from Mac
`http://192.168.11.13:2300/` → 302 /login. Committed to server repo (9c6de41). Device not yet
pointed at it; no admin registered yet; no NPM hostname.
