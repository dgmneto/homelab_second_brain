# Logbook — pihole

Reverse-chronological. Newest entry on top.

## 2026-10-28 — Installed on homelab-notebook
New `nixos/pihole.nix` (pihole-ftl + pihole-web, StevenBlack list, upstreams 1.1.1.1/1.0.0.1/9.9.9.9,
DNSSEC, listeningMode ALL, port 80, weekly `pihole-gravity.timer`), imported in `flake.nix`. UI password
in root-only `/etc/pihole-secrets.env` via EnvironmentFile. Deployed (two switches). Verified from casaos
over tailnet and LAN: `doubleclick.net` → `0.0.0.0`, `example.com` resolves, `pi.hole` → node IP;
`/api/auth` with a wrong password → "password incorrect"; gravity 76148 domains; timer next Sun 04:17.
Not done (needs the user): Tailscale admin console DNS settings, moving the UI password into 1Password.
