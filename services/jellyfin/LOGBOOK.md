# Logbook — jellyfin

Reverse-chronological. Newest entry on top.

## 2026-08-06 — pinned static IP 172.21.0.251 (was dynamic)
Jellyfin was deployed (2026-07-04) with no `ipv4_address` on `internalNetwork`. During a full-stack
restart after the HDD migration pause, Docker handed it `172.21.0.5` — sonarr's static address — and
sonarr then failed with `failed to set up container networking: Address already in use`. Pinned
jellyfin to `172.21.0.251` (high, clear of the low static range, same idea as `hermes` at `.250`) in
`/home/dgmneto/homelab/services/jellyfin/compose.yaml`, recreated it, then started sonarr — both up.
NPM proxies to the hostname `"jellyfin"`, so no proxy-host change was needed. Also observed: while the
box was I/O-saturated (21 containers cold-starting on one disk, 60% iowait), jellyfin took ~20 min to
bind 8096 and `nginxIntern` returned 502 the whole time, even though s6 logged
`service-jellyfin successfully started`. Verified after: `https://jellyfin.intern.dgmneto.com` → 302.

## 2026-07-04 — initial deploy
Stood up Jellyfin alongside Plex on the same `/library/media`. `ghcr.io/hotio/jellyfin:latest`,
`internalNetwork`-only (no static IP/macvlan), `PUID=1005`/`PGID=1313` (reused from `plex/.env`),
`/dev/dri` passed through for HW transcode — log confirmed `Added support for device
[/dev/dri/renderD128]`. Config dir `/footage/services/jellyfin/config` required `sudo mkdir` as
`dgmneto` (parent is root-owned; `openclaw` cannot write there or read `/home/dgmneto/homelab` at all —
see the `CLAUDE.md` correction made in this same task). Added proxy hosts in nginxIntern
(`jellyfin.intern.dgmneto.com`) and nginxProd (`jellyfin.3e.dgmneto.com`), both reusing existing
wildcard Let's Encrypt certs, Force SSL + Websockets Support on. User ran the first-run setup wizard,
created the admin account, and confirmed both URLs work and libraries are scanning. Full detail in
[README.md](README.md).
