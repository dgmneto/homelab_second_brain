# Logbook — prowlarr

Reverse-chronological. Newest entry on top. One entry per task that touches **prowlarr** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-22 — Remove prowlarr from VPN, move to internalNetwork
Prowlarr was running in gluetun's network namespace (`network_mode: container:gluetunProtonVPN`), routing all indexer traffic through ProtonVPN. VPN exit IPs were blocking or rate-limiting tracker domains. ISP is Zen Internet (UK) which does minimal voluntary blocking, making VPN unnecessary for prowlarr.

Changed `services/prowlarr/compose.yaml` on server: replaced `network_mode: container:gluetunProtonVPN` with `networks: intern: (internalNetwork)`. Restarted with `docker compose up -d` — container up at `172.21.0.8`. Updated NPM proxy host ID 6 (`prowlarr.intern.dgmneto.com`) via API from `forward_host: gluetun` to `forward_host: prowlarr`. Verified: `https://prowlarr.intern.dgmneto.com` returns 302 (prowlarr login redirect).

qBittorrent remains behind VPN — torrent peers see the IP directly, so VPN is still needed there.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
