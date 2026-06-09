# Logbook — homelab (project-wide)

Reverse-chronological. Newest entry on top. One entry per task that touches the homelab — what
changed, why, commands run on the server, and the verified outcome. Per-service detail also goes in
the matching `services/<svc>/LOGBOOK.md`.

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
