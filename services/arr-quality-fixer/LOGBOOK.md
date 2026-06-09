# LOGBOOK — arr-quality-fixer

## 2026-06-10 — Created service: nightly missing-item quality fixer
New service. Python3 stdlib script on server at
`/home/dgmneto/homelab/services/arr-quality-fixer/arr-quality-fixer.py`. Cron `0 2 * * *`
(dgmneto crontab). For monitored, file-less, already-released items: <48h since added →
search; >=48h → downgrade restrictive profile (SD/720p/UHD) to HD-1080p(4) then search.
Skips unreleased; fresh-release (<48h aired/released) = search only. Sonarr searches
per-episode (batched per series), profile change per-series. Radarr per-movie.

First live run: Sonarr 42 missing → 3 series (Hacks, Rick and Morty, Your Friends &
Neighbors) downgraded UHD→1080p, 42 episode searches. Radarr 2 missing → The End of Oak
Street skipped (unreleased), Bad Genius downgraded UHD→1080p + searched. Verified Hacks
qualityProfileId now 4 via API. Exit 0.

Log lives in the service dir (not `/footage` — root-owned, dgmneto lacks write w/o sudo).
