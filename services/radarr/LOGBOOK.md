# Logbook — radarr

Reverse-chronological. Newest entry on top. One entry per task that touches **radarr** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-04 — Extra unmanaged file in the Spider-Man: Brand New Day folder
Added a remuxed `[HDR10 hvc1]` copy next to the tracked BTM file (Apple TV can't play `hev1`, see services/plex). Radarr
still tracks only the original. If Radarr upgrades/replaces the movie, delete the hvc1 copy by hand.

## 2026-06-10 — arr-stale-cleaner removes stalled Radarr downloads
New 6-hourly job [arr-stale-cleaner](../arr-maintenance/README.md) removes Radarr queue
items whose qBittorrent torrent has had no `last_activity` in >36h: DELETE from queue
(removeFromClient+blocklist) + MoviesSearch. First run: no Radarr stalls (Bad Genius was
import-pending, skipped). Lives with the quality-fixer under `services/arr-maintenance`.

## 2026-06-10 — Quality profiles auto-downgraded by arr-quality-fixer
New nightly job [arr-quality-fixer](../arr-maintenance/README.md) may change a movie's
`qualityProfileId` to HD-1080p(4) when it's been missing >48h on a restrictive profile
(SD/720p/UHD). First run downgraded Bad Genius from Ultra-HD(5)→1080p + searched; skipped
The End of Oak Street (unreleased). Per-movie MoviesSearch + full-body PUT /movie/{id}.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
