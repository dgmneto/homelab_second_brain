# Access — Plex

- **URLs:** public https://filmin.3e.dgmneto.com (nginxProd) → `plex:32400` — works from LAN (hairpin)
  and the internet (verified 2026-09-22). **`filmin.intern.dgmneto.com` is BROKEN** (verified
  2026-09-22): nginxIntern has no proxy host/cert for it → TLS `unrecognized name`. Plex still
  advertises it in `customConnections`, so clients may try it first and fall back. Direct: `192.168.14.7:32400`
  (macvlan; not reachable from the Docker host).
- **Credential:** `op://Homelab/Plex` (user `dgmneto@gmail.com`) — the Plex account login.
  `op://Homelab/Plex - Claim` is the server *claim* token (onboarding only), NOT a login.
- **Auth:** Plex account (OAuth). User completes login.

Reach via the Claude-in-Chrome extension (see root `../../CLAUDE.md`).
