# arr-quality-fixer

Nightly job that nudges **missing** Sonarr/Radarr items past quality-profile blocks.
A monitored item that never downloads is often blocked because its quality profile is
too strict (e.g. Ultra-HD only, no such release exists). This job searches fresh items
and downgrades older stuck ones to 1080p.

> **Code lives on the server, not in this repo.** Script:
> `/home/dgmneto/homelab/services/arr-quality-fixer/arr-quality-fixer.py`
> (deployment repo `git@github.com:dgmneto/homelab.git`). This second-brain repo holds
> only this runbook + logbook.

## Schedule

`0 2 * * *` in the **dgmneto** user crontab on `homelab`:

```
0 2 * * * /usr/bin/python3 /home/dgmneto/homelab/services/arr-quality-fixer/arr-quality-fixer.py >/dev/null 2>&1
```

Log: `/home/dgmneto/homelab/services/arr-quality-fixer/arr-quality-fixer.log`
(kept off `/footage` — `/footage/services` is root-owned; dgmneto can't write there
without sudo. Log is tiny/append-only.)

## What it does (per app)

For each **monitored, file-less** item from `GET /api/v3/wanted/missing`:

1. **Skip unreleased/unaired.** Radarr: needs `status==released` + a release date in the
   past. Sonarr: needs `airDateUtc` in the past.
2. **Fresh-release guard.** Aired/released within last 48h → **search only**, never
   change profile.
3. **Age split on `added`** (when added to the app; Sonarr episodes use their series'
   `added`):
   - `< 48h` → **search only**.
   - `>= 48h` → **set profile to HD-1080p (id 4)** (if currently restrictive) then search.
4. **Profile guard.** Only downgrades restrictive profiles — **SD(2), HD-720p(3),
   Ultra-HD(5)**. Leaves Any(1), HD-1080p(4), HD-720p/1080p(6), Ultra-HD-Portuguese(7)
   alone (already permit 1080p). Those items are still searched.

Granularity: **Radarr** = per-movie (`MoviesSearch`, `PUT /movie/{id}`). **Sonarr** =
per-**episode** search (`EpisodeSearch`, batched per series), profile change per-**series**
(`PUT /series/{id}`) — Sonarr has no per-episode profile.

## Quality profile ids (same in both apps, +7 Radarr-only)

`1 Any · 2 SD · 3 HD-720p · 4 HD-1080p · 5 Ultra-HD · 6 HD-720p/1080p · 7 Ultra-HD-Portuguese`

## Secrets

API keys read at runtime from each app's `config.xml` (`<ApiKey>`). Nothing hardcoded.

## Manual / debugging

```
# dry-run, no changes — preview decisions
python3 .../arr-quality-fixer.py --dry-run
# one app only
python3 .../arr-quality-fixer.py --app radarr
```

Exit 1 if either app pass errored (app unreachable, e.g. gluetun/NPM down). The other
app still runs. Re-running is safe (idempotent: cheap searches, already-1080p skipped).

## Gotchas

- Sonarr/Radarr have **no host-published ports** — reach them on their internal IPs
  (`sonarr` 172.21.0.5:8989, `radarr` 172.21.0.89:7878). The script uses these directly.
- Radarr `PUT /movie/{id}` and Sonarr `PUT /series/{id}` require the **full** object
  body, not a partial patch — the script GETs then re-PUTs with `qualityProfileId` swapped.
- `wanted/missing` returns aired/released items by default but the script still gates on
  dates defensively.
