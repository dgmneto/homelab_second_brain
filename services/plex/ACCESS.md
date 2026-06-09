# Access — Plex

- **URLs:** https://filmin.intern.dgmneto.com (nginxIntern) and public
  https://filmin.3e.dgmneto.com (nginxProd) — both → `plex:32400`. Direct: `192.168.14.7:32400`
  (macvlan; not reachable from the Docker host).
- **Credential:** `op://Homelab/Plex` (user `dgmneto@gmail.com`) — the Plex account login.
  `op://Homelab/Plex - Claim` is the server *claim* token (onboarding only), NOT a login.
- **Auth:** Plex account (OAuth). User completes login.

Reach via the Claude-in-Chrome extension (see root `../../CLAUDE.md`).
