# arr-quality-fixer — design

Daily 2am job that nudges missing Sonarr/Radarr items so the quality profile stops
blocking them: search recently-added items, downgrade older stuck ones to 1080p.

## Goal

Items that are monitored but never downloaded are often blocked because their quality
profile is too strict (e.g. only Ultra-HD releases accepted, none exist). This job:

- Searches recently-added missing items (they may just not have been searched yet).
- For older still-missing items, relaxes the quality profile to 1080p, then searches.
- Never touches items that are not yet released/aired.

## Runtime

- **Language:** Python 3 (stdlib only — `urllib`, `xml.etree`, `json`, `datetime`,
  `argparse`, `logging`). Host has Python 3.11.2.
- **Location:** new service dir on the **server**:
  `/home/dgmneto/homelab/services/arr-quality-fixer/` (version-controlled with the
  deployment repo on the server, NOT this second-brain repo). Holds
  `arr-quality-fixer.py` + a `README.md`. This second-brain repo only gets the
  `services/arr-quality-fixer/README.md` runbook + logbook, no code.
- **Schedule:** `0 2 * * *` in the **dgmneto** user crontab.
- **Logging:** append to `/footage/services/arr-quality-fixer/arr-quality-fixer.log`
  (under `/footage`, the 492G config mount). One run = one block, timestamped, with a
  summary line.
- **Secrets:** API keys read at runtime from each app's `config.xml`
  (`/footage/services/{sonarr,radarr}/config/config.xml`, `<ApiKey>` element).
  No keys baked into the script, cron line, or repo.

## Targets (verified on server 2026-06-10)

| App    | Base URL                  | Missing count | API key source |
|--------|---------------------------|---------------|----------------|
| Sonarr | `http://172.21.0.5:8989`  | 42            | sonarr config.xml |
| Radarr | `http://172.21.0.89:7878` | 2             | radarr config.xml |

Both use API v3 (`/api/v3/...`).

### Quality profiles (identical IDs both apps)

| id | name                | permits 1080p? |
|----|---------------------|----------------|
| 1  | Any                 | yes (skip)     |
| 2  | SD                  | no (downgrade) |
| 3  | HD-720p             | no (downgrade) |
| 4  | HD-1080p            | yes — **target** |
| 5  | Ultra-HD            | no (downgrade) |
| 6  | HD - 720p/1080p     | yes (skip)     |
| 7  | Ultra-HD-Portuguese | yes — Radarr only (skip) |

**Target profile = HD-1080p, id 4** in both apps.

## Logic (per app)

Pull all monitored, file-less items from `GET /api/v3/wanted/missing`
(`monitored=true`, paged, `pageSize=200`, walk `totalRecords`).

For each candidate:

1. **Released/aired gate** — skip if not yet available:
   - Radarr: skip unless `movie.status == "released"` **and** the earliest of
     `digitalRelease`/`physicalRelease`/`inCinemas` that exists is in the past.
   - Sonarr: skip unless episode `airDateUtc` exists and is in the past.
2. **Fresh-release guard** — if the air/release date used above is within the last 48h,
   **search only**, never change profile (don't punish a brand-new release).
3. **Age split** on the `added` timestamp (Radarr `movie.added`; Sonarr `series.added`,
   inherited by its episodes), measured against now:
   - `added < 48h` → **search only**.
   - `added ≥ 48h` → **set profile to HD-1080p (4)** (subject to the profile guard below),
     then **search**.
4. **Profile guard** — only change profile when the current profile is more restrictive
   than 1080p: ids **2 (SD), 3 (HD-720p), 5 (Ultra-HD)**. Leave 1, 4, 6, 7 unchanged
   (they already permit 1080p). Items whose profile is left unchanged are still searched.

### Search & profile-change calls

- **Radarr search:** `POST /api/v3/command {"name":"MoviesSearch","movieIds":[id]}`.
- **Radarr profile change:** `PUT /api/v3/movie/{id}` with the full movie body, only
  `qualityProfileId` mutated to 4 (Radarr requires the full object on PUT).
- **Sonarr search (episode-level, per requirement):**
  `POST /api/v3/command {"name":"EpisodeSearch","episodeIds":[...]}`. Batch all
  qualifying episode ids of a given series into one command.
- **Sonarr profile change:** series-level (Sonarr has no per-episode profile):
  `PUT /api/v3/series/{id}` with full series body, `qualityProfileId` → 4. Apply once
  per series even if several of its episodes qualify.

To avoid hammering: dedupe profile changes per series/movie; batch Sonarr episode
searches per series; small sleep between command POSTs.

## CLI / safety

- `--dry-run` — log every decision (item, classification, action) but make **no**
  POST/PUT calls. Default is live.
- `--app {sonarr,radarr,both}` — default `both`.
- Rollout: run `--dry-run` first, review the log with the user, then install the cron.
- Idempotent: re-running is safe — searches are cheap, profile already-1080p items are
  skipped by the guard.

## Error handling

- Per-item try/except: a failure on one item logs a warning and continues.
- If an app is unreachable (gluetun/proxy/down) the app's whole pass logs an error and
  is skipped; the other app still runs. Non-zero exit if either app pass errored, so a
  future monitor could catch it.
- HTTP non-2xx → logged with status + body snippet.

## Companion job: arr-stale-cleaner (added later, same service dir)

Queue/download management — distinct from the missing-item logic above. Lives alongside
quality-fixer under `services/arr-maintenance/`, sharing `arr_common.py`.

- **Schedule:** every 6h (`0 */6 * * *`).
- **Logic:** for each Sonarr/Radarr queue item still downloading (`amount_left > 0`), look
  up its torrent in qBittorrent by hash (`downloadId` ↔ `hash`). If `now - last_activity
  > 36h` → stale: `DELETE /api/v3/queue/{id}?removeFromClient=true&blocklist=true&
  skipRedownload=true` then re-search (Radarr `MoviesSearch` / Sonarr `EpisodeSearch`).
  Skip `amount_left == 0` (downloaded, import-pending).
- **qBit access:** `docker exec qbittorrent curl http://localhost:9090/api/v2/torrents/info`
  — qBit bypasses auth for localhost, so no creds. qBit has no host-published port (rides
  gluetun ns). `last_activity` (unix ts) freezes when a torrent stalls.

**Overlap handled:** quality-fixer skips any item already in the download queue, so it
never downgrades a profile or re-searches while a grab is active. The two jobs are
otherwise independent.

## Out of scope (YAGNI)

- Cutoff-unmet items (have a file below cutoff) — not touched.
- Per-release inspection to confirm the profile is the actual block — too heavy nightly.
- Notifications/alerting — log file only for now.
- Import-pending torrents (`amount_left == 0` stuck in queue) — a separate problem.
