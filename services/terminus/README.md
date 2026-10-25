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

### Current device (2026-10-25)
Terminus device **id 7**, MAC `7C:4F:AD:20:A9:6C`, firmware **1.8.17**, model `og_plus`,
`firmware_update=false`, refresh 900 s, playlist `device_7`.

### Screens
- **Morning Board** (extension id 1) — weather + Victoria/Piccadilly/Central + Seven Sisters→King's
  Cross commute verdict. Only item on device 7's playlist. Details, sources and gotchas:
  [extensions/morning_board/README.md](extensions/morning_board/README.md).

### Our device: Seeed "TRMNL 7.5\" (OG) DIY Kit" (XIAO ESP32-S3 Plus)
Firmware `DEVICE_MODEL` = `xiao_epaper_display` (Terminus maps it to `og_plus`). Its wake/config button is **D4 (GPIO5)** — from
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
3. **Model mapping is Terminus' job — don't add models.** `app/aspects/firmware/headers/transformers/
   model_name.rb` maps the firmware `Model` header to a catalog model; `xiao_epaper_display` (our kit)
   → **`og_plus`** (2-bit, 4 grays), and missing/unknown headers fall back to `og_plus` too. A local
   `xiao_epaper_display` model I added while debugging was redundant (the real blocker was gotcha 1)
   and was deleted. Device should sit on `og_plus`.
4. **Old firmware (≤1.5.x) calls `/api/setup/` (trailing slash)**; Terminus only routes `/api/setup`.
   A temporary NPM shim (`location = /api/setup/ {...}`) made 1.5.12 work, but it **broke 1.8.x**:
   nginx answers a proxied location ending in `/` with a **301** for the slash-less URI, and the
   firmware won't follow redirects ("API connection cannot be established", NPM log shows
   `- 301` on `/api/setup` with no upstream status). Shim removed 2026-10-25 after the kit was
   flashed to 1.8.17. **Keep proxy host 25's Advanced config empty.** (`rewrite` would not have
   worked either: NPM proxies `$request_uri`.)
5. **Firmware updates must stay off for the kit.** Terminus syncs OG firmware (ESP32-C3 builds) and
   could OTA it to this ESP32-S3; new devices default to `firmware_update=true`. After any
   re-registration: `update device set firmware_update=false where mac_address='7C:4F:AD:20:A9:6C'`.
   Upgrade only over USB (section below).
6. **Never probe `/api/setup` with curl** — any 200 really provisions a device (+ playlist
   `device_<id>` + screen `welcome_<id>`), even with **no `ID` header** (gets a NULL MAC). Happened
   twice (ids 4, 6); cleanup SQL in LOGBOOK. Probe `/up` or `/` instead.
7. `/api/log` returns 422 for firmware 1.5.12's log payload — harmless (logs just aren't stored).
8. **Re-pairing a known device returns a blank key.** `aspects/devices/provisioner.rb`: if the MAC
   exists, `/api/setup` redacts `api_key` unless `firmware_reset` is true. After a USB reflash (which
   wipes the stored key) either delete the device in Terminus first or set its reset flag.
9. **Flasher entry for our kit:** trmnl.com/flash → "Seeed Studio (TRMNL 7.5\" OG DIY Kit)" (ESP32-S3).
   "Seeed Studio (XIAO 7.5\" ePaper Panel)" is the ESP32-C3 kit — wrong chip.
10. NPM access log for this host: `/footage/services/nginxIntern/data/logs/proxy-host-25_access.log`
   — shows device requests (`ESP32HTTPClient`) with status, quickest way to see if the TRMNL reached us.
   Terminus' own log only prints status codes; problem details come back in the response body.

## Reflashing the kit from the Mac (no buttons needed)
The trmnl.com/flash page needs flashing mode, which is hard to hit on this kit. Working method
(2026-10-25): esptool 5.1.0 is installed on the Mac (`python3 -m esptool`). Plug the kit into the Mac
with a **data** USB-C cable and wake it (short press D4) — in deep sleep USB is off, so no
`/dev/cu.usbmodem*` port exists. esptool's software reset puts the S3's USB-Serial/JTAG into download
mode by itself:
```
curl -fsSLO https://trmnl-fw.s3.us-east-2.amazonaws.com/byod/seeed_OG_DIY_Kit/flash/FW1.8.17.bin
python3 -m esptool --chip esp32s3 --port /dev/cu.usbmodem<N> --baud 460800 \
  --before default-reset --after hard-reset write-flash 0x0 FW1.8.17.bin
```
The `flash/` bin is a merged image (bootloader 0x0, partitions 0x8000, app 0x10000) → write at
**0x0**. Get the URL for other versions from `https://trmnl.com/api/firmware/flash` (keyname
`seeed_OG_DIY_Kit`). It wipes NVS (Wi-Fi + API key) → delete the device in Terminus first (gotcha 8),
then re-enter Wi-Fi + server in the portal. Fallback if the port never appears: on the XIAO board
hold **B**, tap **R**, release **B**.

## Checks
```
cd ~/homelab/services/terminus && docker compose ps            # 4 Up (healthy) + init Exited (0)
curl -s -o /dev/null -w '%{http_code}\n' https://terminus.intern.dgmneto.com/   # from Mac: 302 -> /login
```
`/up` returns 302 too (healthcheck uses `curl --fail`, which accepts it). A bogus
`/api/setup` call with a fake MAC returns a 404 "model_id not-null" problem — expected, not a fault.

Upstream docs say Docker ≥ 29.4.2 / Compose ≥ 5.1.2; casaos has Docker 28.0.1 / Compose 2.34.0 and
the pre-built images run fine (the requirement is for building).
