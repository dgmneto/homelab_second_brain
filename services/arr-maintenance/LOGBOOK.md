# LOGBOOK — arr-maintenance

## 2026-06-15 — Fixed stale-cleaner: dead no-metadata torrents slipped through
~Week-in review. Cron ran clean every 6h for 5 days (zero failures; removed 1 more stall,
Rick&Morty S09E04 queuedDL, on 06-13). But ~18-19 Sonarr queue items sat stuck the whole
time, logged each run as "complete, import pending" and never cleaned. Investigated:
qBit showed them as `metaDL`/`queuedDL` with `size=0, progress=0, amount_left=0,
completion_on=-1` — dead releases that **never fetched metadata** (grabbed by the profile
downgrades), NOT completed downloads.

Two bugs in v1 stale-cleaner, both fixed:
1. **`amount_left==0` treated as "complete"** — false for 0-byte/no-metadata torrents.
   Now use `is_complete()` = `progress>=1 or completion_on>0`.
2. **`last_activity` sentinel** — for never-started torrents qBit returns a sentinel
   (saw negative idle, -494786h), so `now-last_activity>36h` was never true. New
   `idle_seconds()` falls back to `added_on` when last_activity isn't a sane past ts.

Deployed + dry-ran (18 flagged stale, idle 93–357h; 1 spared at 19.3h) then LIVE:
removed+blocklisted+re-searched 18, queue 19→1, exit 0. Re-searches grabbed *different*
releases (e.g. Hacks S01E10 `eztv re` vs blocklisted `rartv`); Rick&Morty S09E04 actively
downloading. Pipeline now self-correcting.

## 2026-06-10 — Added arr-stale-cleaner; consolidated into arr-maintenance
Added second job `arr-stale-cleaner.py` (queue/download management, distinct from the
quality fixer). Every 6h (`0 */6 * * *`): for each Sonarr/Radarr queue item still
downloading (`amount_left>0`), look up its torrent in qBittorrent by hash; if
`now - last_activity > 36h` → DELETE from queue (`removeFromClient&blocklist&skipRedownload`)
+ trigger re-search. qBit reached via `docker exec qbittorrent curl localhost:9090`
(localhost auth-bypass, no creds — qBit has no host-published port, rides gluetun ns).

Refactored shared code into `arr_common.py` (ArrClient, read_api_key, parse_dt, constants,
queue_ids). Renamed the service dir `arr-quality-fixer` → `arr-maintenance` (holds both
jobs + the lib). Updated both crontab paths; old dir removed on server.

Overlap fix in quality-fixer: now skips any item already in the download queue (no
downgrade/search while a grab is active) — uses `queue_ids()`.

Verified: stale-cleaner dry-run then LIVE found 2 genuine stalls (Hacks S01E02, S01E03 —
`stalledDL`, 214.7h idle), removed+blocklisted+re-searched, exit 0. 40 import-pending
torrents (`amount_left==0`) correctly skipped. quality-fixer dry-run afterward skipped
41/42 as "in download queue" (overlap working).

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
