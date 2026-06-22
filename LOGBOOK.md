# Logbook — homelab (project-wide)

Reverse-chronological. Newest entry on top. One entry per task that touches the homelab — what
changed, why, commands run on the server, and the verified outcome. Per-service detail also goes in
the matching `services/<svc>/LOGBOOK.md`.

## 2026-06-22 — prowlarr: move off VPN to internalNetwork
Prowlarr was routing indexer traffic through ProtonVPN (gluetun netns). VPN exit IPs were blocking tracker domains. Zen Internet (UK ISP) does minimal voluntary blocking so VPN is unnecessary for HTTP indexer queries. Moved prowlarr to `internalNetwork` directly; updated NPM proxy host to forward to `prowlarr:9696` instead of `gluetun:9696`. Verified reachable at `prowlarr.intern.dgmneto.com`.
Detail: [services/prowlarr/LOGBOOK.md](services/prowlarr/LOGBOOK.md).

## 2026-06-22 — hermes: add read-only Docker access via socket proxy
Added `tecnativa/docker-socket-proxy` sidecar to hermes compose. Hermes reads Docker API
(containers, images, networks, volumes, info) via `tcp://hermes-docker-proxy:2375` — no write
or exec endpoints exposed. Both containers up and healthy.
Detail: [services/hermes/LOGBOOK.md](services/hermes/LOGBOOK.md).

## 2026-06-22 — watchtower: switch from 30s interval to weekly cron
Hermes gateway was restarting constantly (26+ times on 2026-06-21). Root cause: upstream
`nousresearch/hermes-agent:latest` publishes new images every ~10 minutes during active dev;
watchtower at `--interval 30` picked up every one. Changed watchtower schedule to
`--schedule "0 0 10 * * 0"` (Sundays 10:00 UTC) across all containers. Next update:
2026-06-28. Detail: [services/watchtower/LOGBOOK.md](services/watchtower/LOGBOOK.md).

## 2026-06-15 — New service: Hermes AI agent (Telegram + OpenRouter)
Deployed `nousresearch/hermes-agent` as a new compose service on the server
(`/home/dgmneto/homelab/services/hermes/`), config at `/footage/services/hermes/config`. Wired
Telegram bot (new token) + dedicated OpenRouter key (both stored in 1Password Personal). Telegram
allowlist (2 users + 2 groups) copied from the existing `openclaw` agent's config. Isolation via
container hardening only (no new Linux user) — see `services/hermes/README.md` and
`services/hermes/LOGBOOK.md` for full detail. Verified: telegram connected, ~180MB/2GB RAM idle.

## 2026-06-15 — arr-stale-cleaner fix: dead no-metadata torrents weren't cleaned
One-week review of the arr-maintenance crons. Both ran clean every 6h for 5 days (no
failures). But the stale-cleaner left ~18 Sonarr queue items stuck the whole week, logged
as "complete, import pending". Turned out they were `metaDL`/`queuedDL` torrents that never
fetched metadata (`size=0, progress=0, amount_left=0`) — dead releases the profile
downgrades grabbed, not completed downloads. Two v1 bugs fixed: (1) completion judged by
`progress>=1`/`completion_on>0` instead of `amount_left==0`; (2) `idle_seconds()` falls
back to `added_on` when qBit's `last_activity` is a never-started sentinel (was producing
negative idle, so stalls never flagged). Live run cleaned 18 (remove+blocklist+re-search),
queue 19→1; re-searches grabbed different releases. Touched sonarr, qbittorrent. Detail:
[services/arr-maintenance/LOGBOOK.md](services/arr-maintenance/LOGBOOK.md).

## 2026-06-10 — New service arr-maintenance: quality-fixer + stale-cleaner
Built two host cron jobs (deployment repo `services/arr-maintenance/`, Python3 stdlib,
shared `arr_common.py`) to keep the arr pipeline unstuck. API keys read from each
`config.xml` at runtime; logs beside the scripts.

**arr-quality-fixer** (daily `0 2 * * *`): for monitored, file-less, released/aired items
NOT in the download queue — <48h since added (or aired/released) → search; >=48h → set
restrictive profile (SD/720p/UHD) to HD-1080p(4) then search. Sonarr per-episode search
(batched per series) + per-series profile change; Radarr per-movie. First live run: 3
Sonarr series + 1 Radarr movie downgraded off Ultra-HD, 42 ep + 1 movie searches, 1
unreleased skipped (exit 0).

**arr-stale-cleaner** (every 6h `0 */6 * * *`): for each Sonarr/Radarr queue item still
downloading, match its torrent in qBittorrent by hash; `now - last_activity > 36h` →
remove from queue (`removeFromClient&blocklist&skipRedownload`) + re-search. qBit reached
via `docker exec qbittorrent curl localhost:9090` (localhost auth-bypass, no creds; rides
gluetun ns, no host port). First live run removed 2 stalls (Hacks S01E02/E03, 214.7h idle),
blocklisted + re-searched (exit 0).

Overlap: quality-fixer skips anything already in the download queue (won't downgrade/search
an active grab). Full runbook:
[services/arr-maintenance/README.md](services/arr-maintenance/README.md). Touched sonarr,
radarr (profiles + searches), qbittorrent (stale torrents removed).

## 2026-06-10 — Symlinked harness memory dir to repo `notes/`
Made `notes/` the actual auto-memory store: gave each note harness frontmatter + a `notes/MEMORY.md`
index, then symlinked the harness path
(`~/.claude/projects/-Users-dgmneto-homelab/memory` → `/Users/dgmneto/homelab/notes`). Auto-recall now
reads the real repo files and new memories land in-repo. Old memory dir backed up to `memory.bak.<ts>`.
Symlink is Mac-local/per-machine (not in git) — recreate steps in `notes/README.md`.

## 2026-06-10 — Migrated agent memory into repo `notes/`
Moved the three `~/.claude` project memories (ssh-access, footage-disk-leak, qbittorrent-mass-stop)
into version-controlled `notes/` with a `notes/README.md` index; CLAUDE.md now points there and names
`notes/` the home for durable cross-cutting facts. Reduced the external memory files to recall pointers
(the harness memory dir is a fixed path, can't be relocated — but the repo is now the single source of
truth and the pointers route agents here).

## 2026-06-10 — Added self-improvement mandate to CLAUDE.md
Added a top-of-file "this repo is built for agents to improve" section: every agent must correct stale
docs in the same task, capture mistaken assumptions where the next agent will hit them, restructure
freely, and prefer durable root-cause fixes over perpetual warnings.

## 2026-06-10 — Investigated "all qBittorrent downloads paused"
Drove WebUI via Claude-in-Chrome: all 28 torrents `Stopped`/0 B/0%, but VPN+disk+config
all healthy (green connectivity, 889 GiB free, auto-start OFF). Root cause: `watchtower`
auto-updated the unpinned qbit `:latest` (build-date 2026-06-08), recreated the
container, torrents came back stopped. No state change made. Added a stopped-downloads
decision-table runbook to `services/qbittorrent/README.md`. See its LOGBOOK for detail.

## 2026-06-10 — Split access docs to per-service ACCESS.md
Moved per-service access detail (URL, `op://` credential, auth method, quirks) out of the root
`ACCESS.md` into `services/<svc>/ACCESS.md` for 11 UI services (overseerr, plex, sonarr, radarr,
prowlarr, bazarr, qbittorrent, homeassistant, z2mqtt, nginxIntern, nginxProd). Root `ACCESS.md` is now
an index + shared vault/Chrome notes.

## 2026-06-10 — Overseerr login tested via Chrome tab
Drove the Claude-on-Chrome tab to `overseerr.intern.dgmneto.com`: reachable, renders the sign-in page
with "Use your Plex account" (OAuth) and "Use your Overseerr account" (local) buttons — not currently
authenticated. Did not complete login: entering credentials to authenticate is out of scope (user
performs it). Confirms the Chrome-tab access path works end to end up to the auth boundary.

## 2026-06-10 — Vault UI logins added; verified op access
User moved credentials into the `Homelab` vault — now 11 items, including LOGIN entries for qbittorrent,
Sonarr, Radarr, Prowlarr, Plex, nginx (intern NPM), NGINX Prod. Verified `op` can read them (usernames +
password fields present; values not revealed). Updated `ACCESS.md` to reference `op://Homelab/<item>`
per service. Still missing: Bazarr, HA, Zigbee2MQTT. qBittorrent pw now in vault but still hardcoded in
watchdog.py — flagged to reconcile.

## 2026-06-10 — Service access map (URLs ↔ credential source)
Asked to log into Overseerr using a password from `op`. Not possible: Overseerr uses Sign-in-with-Plex
OAuth and the `Homelab` vault has only 4 infra secrets (no app-UI logins). Also did not perform the
login (interactive password auth is out of scope). Instead pulled the authoritative proxy hostnames
from both NPM sqlite DBs and wrote `ACCESS.md` mapping each service URL to where its credential actually
lives, flagging that op holds no UI passwords (and qBittorrent's is hardcoded in watchdog.py).

## 2026-06-10 — Documented Chrome-extension UI access
Verified service web UIs are reachable through the Claude-in-Chrome extension driving the user's local
Chrome (loaded `overseerr.intern.dgmneto.com/login` successfully). Documented the access flow and the
NPM hostname scheme (`<svc>.intern.dgmneto.com` internal, public via nginxProd) in `CLAUDE.md`.

## 2026-06-10 — Enabled linger for dgmneto
Ran `loginctl enable-linger dgmneto` so the `plex-qbittorrent-watchdog` user service survives logout
(was `Linger=no`, only alive via open sessions). Now `Linger=yes`, service still active. Server change.

## 2026-06-10 — Tested `op` CLI, documented secret access
Verified the 1Password `op` CLI (v2.30.3) works via desktop-app integration (no manual signin).
Confirmed `op vault list` / `op item list` / search against the `Homelab` vault. Added a "Secrets"
section to `CLAUDE.md` with access/search commands and a no-secrets-in-repo rule. Did not extract any
secret values (classifier blocked a test read; not needed). Noted there is no qBittorrent item in the
vault yet.

## 2026-06-10 — Found the Plex→qBittorrent pause job
The "pause downloads while Plex streams" job the user remembered is **not cron** — it is the
`plex-qbittorrent-watchdog` `systemd --user` service (active since 2026-04-29). Documented it under
`services/plex-qbittorrent-watchdog/`, cross-linked from plex/qbittorrent READMEs and the cron note.
Flagged a leaked hardcoded `QBITTORRENT_PASSWORD` in the deployment repo's `watchdog.py` and the
`Linger=no` fragility. No server change.

## 2026-06-09 — Documented cron jobs + commit/push rule
Added the "commit and push ASAP" rule to `CLAUDE.md`. Probed all scheduled jobs on the server and
documented them under `cron/` (README + LOGBOOK). Homelab-specific: root weekly `backup.sh`
(auto-push of deployment repo, Sun 05:00) and openclaw chrome-debug band-aid (daily 03:00, harmless).
No server state changed.

## 2026-06-09 — Hello World
Logbook initiated. Knowledge base scaffolded: root `CLAUDE.md`, `services/<svc>/README.md` for all
18 services, and logbooks (root + per service). No server state changed.
