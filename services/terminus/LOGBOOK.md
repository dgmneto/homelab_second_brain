# Logbook — terminus

Reverse-chronological. Newest entry on top. One entry per task that touches **terminus** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-25 — Fix "API connection cannot be established"; remove exposed IPs
Symptom: TRMNL (Seeed DIY kit) on Wi-Fi but no API. NPM log showed it reaching us over HTTPS fine;
`/api/setup` → 404 `Null value in column "model_id"`. Root causes:
1. My compose bind-mounted empty `/footage/services/terminus/certs` over `/etc/ssl/certs` → no CA
   certs → worker's model sync to trmnl.com failed TLS → `model` table empty. Fix: named volume
   `certificates` (as upstream), removed the host dir. Ran Model/Firmware/Font synchronizers by hand
   via `hanami console` → 61 models.
2. Device sends `Model: xiao_epaper_display`, absent from TRMNL's catalog. Inserted local model
   (id 63) cloned from `og_png` incl. `model_palette` rows, `kind='terminus'` (sync won't delete it):
   `INSERT INTO model (...) SELECT 'xiao_epaper_display', 'Seeed XIAO 7.5" DIY Kit (1-bit)', ..., 'terminus', ... FROM model WHERE name='og_png'`
   + `INSERT INTO model_palette (model_id, palette_id) SELECT 63, palette_id FROM model_palette WHERE model_id=2`.
Also per user: removed host port 2300 and macvlan 192.168.14.40; only path is nginxIntern.
Server repo commit 4c396c1. Device registration not yet observed at time of writing (device backed
off after failures; needs a wake press).

## 2026-10-25 — Device API over HTTPS
`API_URI` → `https://terminus.intern.dgmneto.com` (.env + env.tpl), recreated web+worker, healthy.
Checked: hostname resolves to nginxIntern via router and 1.1.1.1; `/api/setup` over HTTPS returns the
app's own JSON (TLS verify OK); plain http → 301. Firmware uses `setInsecure()` (encrypted, cert not
verified). No device registered yet at time of change (`device` table empty).

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
