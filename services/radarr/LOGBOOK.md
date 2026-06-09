# Logbook — radarr

Reverse-chronological. Newest entry on top. One entry per task that touches **radarr** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-10 — Quality profiles auto-downgraded by arr-quality-fixer
New nightly job [arr-quality-fixer](../arr-quality-fixer/README.md) may change a movie's
`qualityProfileId` to HD-1080p(4) when it's been missing >48h on a restrictive profile
(SD/720p/UHD). First run downgraded Bad Genius from Ultra-HD(5)→1080p + searched; skipped
The End of Oak Street (unreleased). Per-movie MoviesSearch + full-body PUT /movie/{id}.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
