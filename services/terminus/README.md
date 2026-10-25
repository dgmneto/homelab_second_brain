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
- Data (bind mounts): `/footage/services/terminus/{postgres,valkey,fonts,uploads,certs}`.
  `/footage/services` is root-owned and `dgmneto` has no passwordless sudo — dirs were created via a
  throwaway container: `docker run --rm -v /footage/services:/s alpine mkdir -p /s/terminus/...`
  (fonts/uploads chowned to uid 1000 = the image's `app` user).

## Containers
| Container | Image | Notes |
|---|---|---|
| `terminus` (web, puma) | `ghcr.io/usetrmnl/terminus:${TERMINUS_VERSION}` | host port **2300**; also on `internalNetwork` |
| `terminus-worker` (sidekiq) | same | starts only after web is healthy |
| `terminus-db` | `postgres:18.6-alpine` | not published |
| `terminus-valkey` | `valkey/valkey:9.1-alpine` | not published, 256 MB maxmemory |
| `terminus-init-certificates-1` | same as web | one-shot, `Exited (0)` is normal |

terminus containers carry `com.centurylinklabs.watchtower.enable=false`: the project is beta with
breaking changes between versions and device firmware compatibility gates. **Upgrade deliberately**:
check upstream release notes, bump `TERMINUS_VERSION` in `.env` **and** `env.tpl`, `docker compose up -d`
(migrations run on web start). DB/valkey tags are pinned in compose.

## Access
- UI + device API: **http://192.168.11.13:2300** (LAN only, plain HTTP). `API_URI` is set to this —
  the device and server must use the same URI. If casaos' IP changes, update `API_URI`.
- First account to **Register** becomes the verified admin; later sign-ups need manual verification.
- **https://terminus.intern.dgmneto.com** — nginxIntern proxy host id 25 → `terminus:2300`
  (docker DNS on `internalNetwork`, wildcard cert id 1, SSL forced). Created 2026-10-25 via the NPM API
  (recipe in `services/nginxIntern/README.md`). Use this for the browser UI.
- The device keeps using the plain-IP `API_URI` (no TLS / proxy dependency for the ESP32). Switching
  the device to the hostname would mean changing `API_URI` too, since both must match.

### Networking choice (house standard)
Web container joins **`internalNetwork`** (no static IP) and NPM proxies to it by container name —
the same pattern as sonarr/radarr/overseerr/jellyfin. **macvlan** (`192.168.14.0/24`, VLAN 14) is
reserved for containers that need their own LAN L2 presence: plex (discovery), homeassistant,
mosquitto, z2mqtt, matter, and the two NPMs. Terminus doesn't need that; port 2300 on the host IP
covers the device. Note the macvlan host-isolation gotcha: casaos itself can't reach macvlan IPs.

## Pointing the TRMNL at it
Hold the device button → captive portal Wi-Fi `TRMNL` on phone → pick Wi-Fi, then under custom
server enter `http://192.168.11.13:2300`. Device auto-provisions on its first Display API call.
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

## Checks
```
cd ~/homelab/services/terminus && docker compose ps            # 4 Up (healthy) + init Exited (0)
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.11.13:2300/   # 302 -> /login
```
`/up` returns 302 too (healthcheck uses `curl --fail`, which accepts it). A bogus
`/api/setup` call with a fake MAC returns a 404 "model_id not-null" problem — expected, not a fault.

Upstream docs say Docker ≥ 29.4.2 / Compose ≥ 5.1.2; casaos has Docker 28.0.1 / Compose 2.34.0 and
the pre-built images run fine (the requirement is for building).
