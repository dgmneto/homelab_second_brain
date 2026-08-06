# Logbook — sonarr

Reverse-chronological. Newest entry on top. One entry per task that touches **sonarr** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-08-06 — failed to start: its static IP had been taken by jellyfin
During the full-stack restart after the HDD-migration pause, sonarr failed with
`failed to set up container networking: Address already in use`. Cause: sonarr pins
`ipv4_address: 172.21.0.5`, but `jellyfin` had **no** pinned address and Docker handed it `.5`
dynamically while sonarr was down. Same failure class as hermes stealing nginxProd's `.9` on
2026-08-03. Fixed by pinning jellyfin to `172.21.0.251` (see `../jellyfin/LOGBOOK.md`), then
`docker compose up -d` here — sonarr came up on `.5` and answers `302` on `172.21.0.5:8989`.

**General rule for this box:** on the shared external `internalNetwork` bridge, any container left
without `ipv4_address` can squat a *different* service's static IP whenever start order changes. If a
stack fails with "Address already in use", check
`docker network inspect internalNetwork` for who currently holds the address rather than assuming the
failing container is at fault.

## 2026-06-10 — arr-stale-cleaner removes stalled Sonarr downloads
New 6-hourly job [arr-stale-cleaner](../arr-maintenance/README.md) removes Sonarr queue
items whose qBittorrent torrent has had no `last_activity` in >36h: DELETE from queue
(removeFromClient+blocklist) + per-episode re-search. First run removed Hacks S01E02 &
S01E03 (stalledDL, 214.7h idle). Lives with the quality-fixer under `services/arr-maintenance`.

## 2026-06-10 — Quality profiles auto-downgraded by arr-quality-fixer
New nightly job [arr-quality-fixer](../arr-maintenance/README.md) may change a series'
`qualityProfileId` to HD-1080p(4) when it has stuck missing episodes on a restrictive
profile (SD/720p/UHD). First run downgraded Hacks, Rick and Morty, Your Friends &
Neighbors from Ultra-HD(5)→1080p and triggered per-episode searches (42 eps). Profile
change is series-level (Sonarr has no per-episode profile); search is per-episode.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
