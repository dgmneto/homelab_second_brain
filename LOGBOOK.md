# Logbook — homelab (project-wide)

Reverse-chronological. Newest entry on top. One entry per task that touches the homelab — what
changed, why, commands run on the server, and the verified outcome. Per-service detail also goes in
the matching `services/<svc>/LOGBOOK.md`.

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
