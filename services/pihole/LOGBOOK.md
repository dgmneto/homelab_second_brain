# Logbook — pihole

Reverse-chronological. Newest entry on top.

## 2026-11-24 — Investigation: "pihole not working" → tailnet DNS no longer points at it
Server healthy: `pihole-ftl` active, listening 53/80, gravity 76105 domains (timer ran Sun 11-22),
`dns.blocking.active=true`; on-box `dig @127.0.0.1` / `@100.67.47.127 doubleclick.net` → `0.0.0.0`, live
`gravity blocked` lines in pihole.log. Root cause: `tailscale dns status` shows **"no resolvers configured"**
tailnet-wide — the Pi-hole global nameserver is gone from the Tailscale admin console. Last query per client:
iPhone 100.102.49.41 on 10-30, Apple TV 11-15, divinos-pc 11-20; only LAN 192.168.11.138 still uses it. No change
made (needs admin console). Documented troubleshooting order + gotchas (cloud-session DNS is intercepted,
`pihole status` false "NOT running").

## 2026-10-28 — Installed on homelab-notebook
New `nixos/pihole.nix` (pihole-ftl + pihole-web, StevenBlack list, upstreams 1.1.1.1/1.0.0.1/9.9.9.9,
DNSSEC, listeningMode ALL, port 80, weekly `pihole-gravity.timer`), imported in `flake.nix`. UI password
in root-only `/etc/pihole-secrets.env` via EnvironmentFile. Deployed (two switches). Verified from casaos
over tailnet and LAN: `doubleclick.net` → `0.0.0.0`, `example.com` resolves, `pi.hole` → node IP;
`/api/auth` with a wrong password → "password incorrect"; gravity 76148 domains; timer next Sun 04:17.
Not done (needs the user): Tailscale admin console DNS settings, moving the UI password into 1Password.
