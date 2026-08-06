# Jellyfin

Second media server running alongside [Plex](../plex/README.md) — same `/library/media` library,
independent server/library database. Added 2026-07-04.

## Deployment

- Compose file: `/home/dgmneto/homelab/services/jellyfin/compose.yaml` on the server.
- Image: `ghcr.io/hotio/jellyfin:latest` (hotio image, same family as bazarr/radarr/sonarr — supports
  `PUID`/`PGID`/`UMASK`/`TZ` env vars).
- Config: `/footage/services/jellyfin/config` (bind mount, root-owned dir; hotio's `/init` chowns it to
  `PUID:PGID` on first boot — same pattern as `bazarr`'s config dir).
- Media: `/library/media` mounted read-write at the same container path (matches Plex's mount).
- `PUID=1005` / `PGID=1313` — reused from `plex/.env` so both servers see the same file ownership on
  `/library/media`.
- GPU: `/dev/dri` passed through for hardware transcode (Intel QuickSync via `renderD128`, same device
  Plex uses). Enable HW acceleration in Jellyfin's dashboard → Playback if not already on.
- Network: `internalNetwork` bridge only (no macvlan) — reached purely through the two
  nginx-proxy-manager instances via Docker DNS (`jellyfin:8096`), same pattern as `overseerr`/`bazarr`.
  Port 8096 is **not** published to the host.
- **Static IP `172.21.0.251`** (pinned 2026-08-06). It originally had *no* `ipv4_address`, so Docker
  assigned it dynamically — and during a full-stack restart it grabbed `172.21.0.5`, sonarr's static
  address, making sonarr fail with `failed to set up container networking: Address already in use`.
  Pinned high (like `hermes` at `.250`) to stay clear of the low statically-assigned range. NPM proxies
  to the hostname `"jellyfin"`, not an IP, so the address can change without touching proxy config.

## Access

- Internal: `https://jellyfin.intern.dgmneto.com` (via `nginxIntern`, wildcard `*.intern.dgmneto.com`
  cert, Force SSL).
- Public: `https://jellyfin.3e.dgmneto.com` (via `nginxProd`, wildcard `*.3e.dgmneto.com` cert, Force
  SSL) — mirrors Plex's `filmin.3e.dgmneto.com` public exposure. No DNS wiring needed: `ddns` already
  keeps a wildcard-covering record current for `3e.dgmneto.com`.
- Both proxy hosts have Websockets Support enabled (needed for Jellyfin's live UI updates).
- Login: local Jellyfin account created via the first-run setup wizard (not Plex OAuth — Jellyfin has
  no such SSO). Credentials are **not** in the 1Password `Homelab` vault yet — add them as a new item
  if you want this documented like the other `services/*/ACCESS.md` entries.

## Gotchas

- Unlike Plex, Jellyfin does **not** need a `macvlan` static IP — it has no DLNA/GDM requirement forcing
  direct LAN reachability in this setup, so the simpler `internalNetwork`-only pattern (like overseerr)
  works fine and was used instead. **But "no macvlan" ≠ "no `ipv4_address`"**: leaving the address
  dynamic is what caused the 2026-08-06 collision with sonarr. On this shared external bridge, any
  container without a pinned IP can land on another service's static address whenever it starts first.
- Jellyfin is slow to begin listening on 8096 when the box is I/O-saturated (e.g. all 21 containers
  cold-starting on one disk). `nginxIntern` returns **502** during that window and s6 logs claim
  `service-jellyfin successfully started` while nothing is bound yet — wait for the disk to settle
  before assuming it's broken.
- `/footage/services/jellyfin` had to be created with `sudo mkdir` — `/footage/services` is root-owned,
  and neither `dgmneto` nor the `openclaw` deploy user can write there directly. `openclaw` also turned
  out **not** to have passwordless sudo or read access to `/home/dgmneto/homelab` on this box, despite
  `CLAUDE.md`'s note that it "holds the sudo password" — use `dgmneto`'s own sudo access instead until
  that's sorted out.
