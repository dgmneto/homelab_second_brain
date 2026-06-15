# arr-maintenance

Two host cron jobs that keep the Sonarr/Radarr media pipeline unstuck. They share one
helper module and run on the homelab host.

> **Code lives on the server, not in this repo.** Dir:
> `/home/dgmneto/homelab/services/arr-maintenance/` (deployment repo
> `git@github.com:dgmneto/homelab.git`). This second-brain repo holds only this runbook
> + logbook.

| File | Role |
|------|------|
| `arr_common.py` | shared: `ArrClient`, `read_api_key`, `parse_dt`, app/profile constants, `queue_ids()` |
| `arr-quality-fixer.py` | **daily 2am** — unstick *missing* items blocked by quality profile |
| `arr-stale-cleaner.py` | **every 6h** — remove *stalled downloads*, blocklist, re-search |

Both read API keys from each app's `config.xml` (`<ApiKey>`) at runtime — nothing
hardcoded. Logs sit beside the scripts (`*.log`, gitignored); not on `/footage`
(`/footage/services` is root-owned, dgmneto can't write there without sudo).

Crontab (dgmneto user):
```
0 2 * * *   /usr/bin/python3 /home/dgmneto/homelab/services/arr-maintenance/arr-quality-fixer.py >/dev/null 2>&1
0 */6 * * * /usr/bin/python3 /home/dgmneto/homelab/services/arr-maintenance/arr-stale-cleaner.py >/dev/null 2>&1
```

## Quality profile ids (same both apps; +7 Radarr-only)

`1 Any · 2 SD · 3 HD-720p · 4 HD-1080p (target) · 5 Ultra-HD · 6 HD-720p/1080p · 7 Ultra-HD-Portuguese`
Restrictive (block 1080p, eligible for downgrade): **2, 3, 5**.

---

## arr-quality-fixer (missing items)

A monitored item that never downloads is often blocked because its quality profile is too
strict (e.g. Ultra-HD only, no such release exists). For each **monitored, file-less** item
from `GET /api/v3/wanted/missing` that is **not already in the download queue**:

1. **Skip if in download queue** — never act on something being grabbed (handoff to the
   stale-cleaner). Built from `GET /api/v3/queue` (movieId / episodeId sets).
2. **Skip unreleased/unaired.** Radarr: needs `status==released` + a release date in the
   past. Sonarr: needs `airDateUtc` in the past.
3. **Fresh-release guard.** Aired/released within last 48h → **search only**, never change
   profile.
4. **Age split on `added`** (Sonarr episodes use their series' `added`):
   `< 48h` → **search only**; `>= 48h` → **set profile to HD-1080p (4)** (only if currently
   restrictive: 2/3/5) then search.

Granularity: **Radarr** per-movie (`MoviesSearch`, `PUT /movie/{id}`). **Sonarr** per-**episode**
search (`EpisodeSearch`, batched per series), profile change per-**series** (`PUT /series/{id}`)
— Sonarr has no per-episode profile.

## arr-stale-cleaner (stalled downloads)

Distinct from "missing" — these items *are* in the download queue but stuck. For each
queue item that is **not yet complete** (`progress < 1` and `completion_on <= 0` — see the
gotcha below):

1. Look up its torrent in qBittorrent by hash (`downloadId` ↔ torrent `hash`).
2. Compute **idle = seconds since last progress** (`idle_seconds()`): qBit's
   `last_activity` if it's a sane past timestamp, else fall back to `added_on`. If
   `idle > 36h` → **stale**:
   `DELETE /api/v3/queue/{id}?removeFromClient=true&blocklist=true&skipRedownload=true`
   (deletes torrent + partial data, bans that release), then trigger a fresh search
   (Radarr `MoviesSearch` / Sonarr `EpisodeSearch`). Blocklist guarantees the re-search
   grabs a *different* release.
3. Skip genuinely **complete** items (`progress >= 1` or `completion_on > 0`) — downloaded,
   import-pending, a different problem.

### Reaching qBittorrent (important)

qBit rides the gluetun VPN namespace (`network_mode: container:gluetunProtonVPN`) — its
port 9090 is **not host-published**, only proxied via nginxIntern. The script reaches it
with **`docker exec qbittorrent curl http://localhost:9090/api/v2/torrents/info`**: qBit
**bypasses auth for localhost**, so no credentials are needed (verified — HTTP 200, no
login). dgmneto is in the `docker` group, so no sudo. `last_activity` is a unix timestamp
of the torrent's last piece activity — freezes when a torrent stalls, exactly what "no
progress" means.

## Manual / debugging

```
SVC=/home/dgmneto/homelab/services/arr-maintenance
python3 $SVC/arr-quality-fixer.py --dry-run            # preview, no changes
python3 $SVC/arr-stale-cleaner.py --dry-run
python3 $SVC/arr-stale-cleaner.py --app radarr         # one app only
```

Both exit 1 if an app pass errors (app unreachable, e.g. gluetun/NPM down); the other app
still runs. stale-cleaner exits 1 immediately if qBit can't be read. Re-running is safe
(idempotent: searches are cheap, already-1080p skipped, completed/queued items skipped).

## Gotchas

- Sonarr/Radarr have **no host-published ports** — reach them on internal IPs
  (`sonarr` 172.21.0.5:8989, `radarr` 172.21.0.89:7878). Scripts use these directly.
- Radarr `PUT /movie/{id}` and Sonarr `PUT /series/{id}` require the **full** object body,
  not a partial patch — the script GETs then re-PUTs with `qualityProfileId` swapped.
- qBit `downloadId` from the arr queue is **uppercase**; torrent `hash` is lowercase —
  match case-insensitively.
- An item actively downloading still shows in `wanted/missing` (no file yet); the
  quality-fixer's queue-skip is what prevents double-searching / downgrading it.
- **`amount_left == 0` does NOT mean complete.** A torrent stuck in `metaDL`/`queuedDL`
  with no metadata reports `size=0, progress=0, amount_left=0`. The original v1
  stale-cleaner skipped these as "import pending" and left ~19 dead grabs sitting in the
  queue for a week. Fixed 2026-06-15: completion is judged by `progress >= 1` /
  `completion_on > 0`, not `amount_left`.
- **`last_activity` can be a sentinel** (0 or a far-future value → negative idle) for
  torrents that never started. `idle_seconds()` falls back to `added_on` so a torrent that
  has downloaded nothing since it was added is correctly aged. Without this the no-metadata
  stalls were never flagged (idle came out negative).
