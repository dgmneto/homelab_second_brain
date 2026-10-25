# terminus — TRMNL BYOS server

Self-hosted [usetrmnl/terminus](https://github.com/usetrmnl/terminus) (Hanami/Ruby) so the TRMNL
e-ink display talks to casaos instead of trmnl.com. Deployed 2026-10-25, version **0.78.0**.

## Where things are
- Compose: `/home/dgmneto/homelab/services/terminus/compose.yaml` (adapted from upstream `compose.yml`).
- `.env` (mode 600, gitignored) rendered from `env.tpl` + 1Password item **`op://Homelab/Terminus`**
  (fields `APP_SECRET`, `DATABASE_PASSWORD`, `KEYVALUE_PASSWORD`). Re-render from the Mac:
  ```
  ssh dgmneto@homelab 'cat ~/homelab/services/terminus/env.tpl' | op inject | ssh dgmneto@homelab 'umask 077; cat > ~/homelab/services/terminus/.env'
  ```
  **Never regenerate those passwords** once data exists — Postgres/Valkey keep the first ones and
  the app then fails with `password authentication failed for user "terminus"`.
- Data (bind mounts): `/footage/services/terminus/{postgres,valkey,fonts,uploads}`. CA certs live in
  the **named volume `terminus_certificates`** — see gotcha below; never bind-mount `/etc/ssl/certs`.
  `/footage/services` is root-owned and `dgmneto` has no passwordless sudo — dirs were created via a
  throwaway container: `docker run --rm -v /footage/services:/s alpine mkdir -p /s/terminus/...`
  (fonts/uploads chowned to uid 1000 = the image's `app` user).

## Containers
| Container | Image | Notes |
|---|---|---|
| `terminus` (web, puma) | `ghcr.io/usetrmnl/terminus:${TERMINUS_VERSION}` | **no host port**; internalNetwork **172.21.0.140** only |
| `terminus-worker` (sidekiq) | same | starts only after web is healthy |
| `terminus-db` | `postgres:18.6-alpine` | not published |
| `terminus-valkey` | `valkey/valkey:9.1-alpine` | not published, 256 MB maxmemory |
| `terminus-init-certificates-1` | same as web | one-shot, `Exited (0)` is normal |

terminus containers carry `com.centurylinklabs.watchtower.enable=false`: the project is beta with
breaking changes between versions and device firmware compatibility gates. **Upgrade deliberately**:
check upstream release notes, bump `TERMINUS_VERSION` in `.env` **and** `env.tpl`, `docker compose up -d`
(migrations run on web start). DB/valkey tags are pinned in compose.

## Access
- **`API_URI=https://terminus.intern.dgmneto.com`** (since 2026-10-25) — UI *and* device API go
  through nginxIntern (proxy host id 25 → `terminus:2300`, wildcard LE cert id 1, SSL forced).
  Device custom-server URL must be exactly `https://terminus.intern.dgmneto.com` (no trailing slash;
  `http://` gets a 301 the firmware won't follow). Device and `API_URI` must match.
- This is the house equivalent of trmnl-firmware issue #58 (Caddy + DuckDNS + LE): DNS for
  `*.intern.dgmneto.com` resolves to 192.168.14.34 on **both** the router and public resolvers
  (Cloudflare CNAME → `intern.dgmneto.com`), so the device resolves it with any DNS.
- **TLS caveat:** firmware (`lib/trmnl/include/http_client.h`) calls `setInsecure()` for every https
  URL — traffic is encrypted but the server cert is **not verified** (no MITM protection).
- **No direct/fallback address** (removed 2026-10-25 at user request): no host port, no macvlan IP.
  The only way in is nginxIntern. If NPM is down, the UI and every device are down.
- First account to **Register** becomes the verified admin; later sign-ups need manual verification.

### Networking
Web container: **internalNetwork `172.21.0.140`** (static; nginxIntern → `terminus:2300`) +
**`terminus_default`** (private bridge to db/valkey/worker). Nothing published on the host or LAN.
History: briefly had macvlan `192.168.14.40` + host port 2300 (2026-10-25), removed same day once
the device moved to the HTTPS hostname. To test the backend bypassing NPM, curl from inside:
`docker exec terminus curl -s -o /dev/null -w '%{http_code}' http://localhost:2300/up`.

House standard: internalNetwork for everything proxied by NPM (most with static IPs); macvlan only
when a container needs its own LAN address (plex, homeassistant, mosquitto, z2mqtt, matter, NPMs).

Changing `API_URI`: edit `.env` **and** `env.tpl`, `docker compose up -d web worker`, then re-enter
the custom server URL in the device portal (hold D4 >5 s).

## Pointing the TRMNL at it
Hold the device button → captive portal Wi-Fi `TRMNL` on phone → pick Wi-Fi, then under custom
server enter `https://terminus.intern.dgmneto.com`. Device auto-provisions on its first Display API call.
TRMNL OG needs firmware ≥ 1.8.16; **disable auto firmware updates** after provisioning or it can
stick on the logo screen (upstream doc/devices.adoc).

### Our device: Seeed "TRMNL 7.5\" (OG) DIY Kit" (XIAO ESP32-S3 Plus)
Firmware model `xiao_epaper_display`. Its wake/config button is **D4 (GPIO5)** — from
`trmnl-firmware` `src/display.cpp` device table (`intr`=5) + XIAO S3 pinout (D4=GPIO5). Not BOOT, not
RESET. Press semantics (`src/button.cpp`, `include/config.h`), measured on the press that wakes it:
- hold **>5 s** (release before 15 s) → forget Wi-Fi → captive portal `TRMNL` comes up
- hold **≥15 s** → soft reset (forgets device API key/credentials, then portal)
- double-click → server-assigned special function
RESET (on the XIAO) only reboots; BOOT+power is flashing mode. Reflash/upgrade: https://trmnl.com/flash.

## Gotchas (cost real time — read before debugging "API connection cannot be established")
1. **Empty CA store → devices can't register.** A bind mount of an empty host dir over
   `/etc/ssl/certs` hides the image's 301 CA certs. Outbound TLS then fails (`certificate verify
   failed (unable to get local issuer certificate)` in `docker logs terminus-worker`), the nightly
   model sync from `https://trmnl.com/api/models` never populates the `model` table, and
   `/api/setup` returns 404 `Null value in column "model_id"`. Fixed by a named volume (Docker seeds
   it from the image). Check: `docker exec terminus ls /etc/ssl/certs | wc -l` (~301).
2. **Syncs run on cron only** (`config/sidekiq_scheduler.yml`: models + fonts daily at 00:00, firmware
   6-hourly). On a fresh install, force them instead of waiting:
   ```
   echo 'Terminus::Jobs::Synchronizers::Model.new.perform' | docker exec -i terminus bundle exec hanami console
   ```
   (same for `::Firmware` and `::Font`). Check: `select count(*) from model` (~61).
3. **The Seeed DIY kit's model isn't in TRMNL's catalog.** Firmware sends `Model: xiao_epaper_display`;
   trmnl.com/api/models has no `xiao_*`. Terminus matches the header to `model.name` exactly, else
   404 `model_id` not-null. Fix applied: local model **id 63 `xiao_epaper_display`**, clone of
   `og_png` (800x480, 1-bit, same palettes), `kind='terminus'` — the sync only deletes kinds
   byod/kindle/tidbyt/trmnl, so it survives. Recreate if the DB is ever rebuilt (SQL in LOGBOOK).
4. **Old firmware calls `/api/setup/` (trailing slash)**; Terminus only routes `/api/setup` → 404
   HTML page (Length 1064 in the NPM log). Our kit shipped with **firmware 1.5.12**. Fixed in NPM
   proxy host 25 *Advanced* config with an exact `location = /api/setup/ { ... proxy_pass
   $forward_scheme://$server:$port/api/setup$is_args$args; }`. A plain `rewrite` does **not** work:
   NPM's `proxy.conf` uses `proxy_pass ...$request_uri`, which always forwards the original path.
5. **Firmware 1.5.12 sends no `Model` header** → Terminus defaults the device to `og_plus`. Device
   id 5 (`7C:4F:AD:20:A9:6C`, label "Seeed XIAO DIY") was manually set to model
   `xiao_epaper_display` and **`firmware_update=false`**: Terminus syncs OG firmware (ESP32-C3
   builds) for og_* models — must never be OTA'd to this ESP32-S3 board. Upgrade the kit only via
   https://trmnl.com/flash (USB) choosing the XIAO/DIY-kit build. Once on ≥1.8.x it sends
   `Model: xiao_epaper_display` and the `/api/setup/` shim becomes unnecessary.
6. **Don't test `/api/setup` with curl + fake MAC** — on success it really provisions a device
   (+ playlist `device_<id>`). Happened once (id 4, MAC 00:00:00:00:00:00), deleted by SQL.
7. `/api/log` returns 422 for firmware 1.5.12's log payload — harmless (logs just aren't stored).
8. **Re-pairing a known device returns a blank key.** `aspects/devices/provisioner.rb`: if the MAC
   exists, `/api/setup` redacts `api_key` unless `firmware_reset` is true. After a USB reflash (which
   wipes the stored key) either delete the device in Terminus first or set its reset flag.
9. **Flasher entry for our kit:** trmnl.com/flash → "Seeed Studio (TRMNL 7.5\" OG DIY Kit)" (ESP32-S3).
   "Seeed Studio (XIAO 7.5\" ePaper Panel)" is the ESP32-C3 kit — wrong chip.
10. NPM access log for this host: `/footage/services/nginxIntern/data/logs/proxy-host-25_access.log`
   — shows device requests (`ESP32HTTPClient`) with status, quickest way to see if the TRMNL reached us.
   Terminus' own log only prints status codes; problem details come back in the response body.

## Checks
```
cd ~/homelab/services/terminus && docker compose ps            # 4 Up (healthy) + init Exited (0)
curl -s -o /dev/null -w '%{http_code}\n' https://terminus.intern.dgmneto.com/   # from Mac: 302 -> /login
```
`/up` returns 302 too (healthcheck uses `curl --fail`, which accepts it). A bogus
`/api/setup` call with a fake MAC returns a 404 "model_id not-null" problem — expected, not a fault.

Upstream docs say Docker ≥ 29.4.2 / Compose ≥ 5.1.2; casaos has Docker 28.0.1 / Compose 2.34.0 and
the pre-built images run fine (the requirement is for building).
