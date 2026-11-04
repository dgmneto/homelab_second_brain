# Access — Plex

- **URLs:** public https://filmin.3e.dgmneto.com (nginxProd) → `plex:32400` — works from LAN (hairpin)
  and the internet (verified 2026-09-22). **`filmin.intern.dgmneto.com` is BROKEN** (verified
  2026-09-22): nginxIntern has no proxy host/cert for it → TLS `unrecognized name`. Plex still
  advertises it in `customConnections`, so clients may try it first and fall back. Direct: `192.168.14.7:32400`
  (macvlan; not reachable from the Docker host).
- **Token-free LAN access:** Preferences `allowedNetworks="192.168.0.0/16"` → any LAN client (e.g. Hermes on
  homelab-notebook) can call the API at `http://192.168.14.7:32400` with no `X-Plex-Token` (verified
  2026-11-04: `/status/sessions`, `/transcode/sessions`, `/library/sections` → 200). `plex.intern.dgmneto.com`
  does **not** exist.
- **Credential:** `op://Homelab/Plex` (user `dgmneto@gmail.com`) — the Plex account login.
  `op://Homelab/Plex - Claim` is the server *claim* token (onboarding only), NOT a login.
- **Auth:** Plex account (OAuth). User completes login.

Reach via the Claude-in-Chrome extension (see root `../../CLAUDE.md`).
