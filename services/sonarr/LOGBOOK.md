# Logbook — sonarr

Reverse-chronological. Newest entry on top. One entry per task that touches **sonarr** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-10 — Quality profiles auto-downgraded by arr-quality-fixer
New nightly job [arr-quality-fixer](../arr-quality-fixer/README.md) may change a series'
`qualityProfileId` to HD-1080p(4) when it has stuck missing episodes on a restrictive
profile (SD/720p/UHD). First run downgraded Hacks, Rick and Morty, Your Friends &
Neighbors from Ultra-HD(5)→1080p and triggered per-episode searches (42 eps). Profile
change is series-level (Sonarr has no per-episode profile); search is per-episode.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
