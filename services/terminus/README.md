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
| `terminus` (web, puma) | `ghcr.io/usetrmnl/terminus:${TERMINUS_VERSION}` | host port **2300**; macvlan **192.168.14.40**; internalNetwork **172.21.0.140** |
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
- Direct fallbacks still work: `http://192.168.14.40:2300` (macvlan) and `http://192.168.11.13:2300`
  (host port). If NPM is down, devices break — to decouple, switch `API_URI` back to one of those
  and re-enter the URL in the device portal.
- First account to **Register** becomes the verified admin; later sign-ups need manual verification.

### Networking
Web container has three networks (2026-10-25):
- **macVlanNetwork `192.168.14.40`** — its own LAN IP on VLAN 14 (`http://192.168.14.40:2300`).
  Picked by ping/arp-probing; matches the house pattern of pairing last octets (`.40` ↔ `.140`).
- **internalNetwork `172.21.0.140`** — static, how nginxIntern reaches it (`terminus:2300`).
- **`terminus_default`** — private bridge to db/valkey/worker; host port 2300 is published via it,
  so `http://192.168.11.13:2300` (the URI the device was paired with) keeps working.
Macvlan gotcha: casaos itself cannot reach `192.168.14.40` (macvlan host isolation) — test it from
the Mac, not from an SSH session on the server.

House standard: internalNetwork for everything proxied by NPM (most with static IPs); macvlan added
only when a container should have its own LAN address (plex, homeassistant, mosquitto, z2mqtt,
matter, both NPMs, now terminus).

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

## Checks
```
cd ~/homelab/services/terminus && docker compose ps            # 4 Up (healthy) + init Exited (0)
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.11.13:2300/   # 302 -> /login
```
`/up` returns 302 too (healthcheck uses `curl --fail`, which accepts it). A bogus
`/api/setup` call with a fake MAC returns a 404 "model_id not-null" problem — expected, not a fault.

Upstream docs say Docker ≥ 29.4.2 / Compose ≥ 5.1.2; casaos has Docker 28.0.1 / Compose 2.34.0 and
the pre-built images run fine (the requirement is for building).
