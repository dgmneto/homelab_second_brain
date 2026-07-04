# Logbook — jellyfin

Reverse-chronological. Newest entry on top.

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
