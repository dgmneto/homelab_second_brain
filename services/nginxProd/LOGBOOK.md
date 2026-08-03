# Logbook — nginxProd

Reverse-chronological. Newest entry on top. One entry per task that touches **nginxProd** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-08-03 — Recover from IP collision after forced reboot
Homelab was unresponsive (ARP `incomplete`, no route) after a 13-day silent hang caused by bad sectors
on both `library`-array disks (see [notes/disk-health-storage-array.md](../../notes/disk-health-storage-array.md));
user power-cycled the box. Post-boot, `nginxProxyManagerProd` failed to (re)start: `docker inspect`
showed `failed to set up container networking: Address already in use` on its static IP `172.21.0.9`
(internalNetwork), and the container got stuck in `Removal In Progress`. Cause: `hermes` (no static IP)
had been dynamically assigned `172.21.0.9` on this boot. Fix: pinned `hermes` to `172.21.0.250` in
`../hermes/compose.yaml` (`docker compose up -d` there), which freed `.9`; re-ran
`docker compose up -d` here and the container came up clean under its proper name (the zombie
`<hash>_nginxProxyManagerProd` cleared on its own once the address was free). Verified: `docker ps`
shows `nginxProxyManagerProd Up`, `curl --resolve filmin.3e.dgmneto.com:443:192.168.14.33 -k` against
it returns `HTTP 401` (proxy responding). Documented the collision pattern + fix in this service's
README quirks section.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
