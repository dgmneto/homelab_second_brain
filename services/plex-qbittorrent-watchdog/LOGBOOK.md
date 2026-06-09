# Logbook — plex-qbittorrent-watchdog

Reverse-chronological. Newest entry on top. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-10 — Enabled linger
Ran `loginctl enable-linger dgmneto` on the server (no sudo needed — polkit allows own-user). Now
`Linger=yes`, marker `/var/lib/systemd/linger/dgmneto` present, watchdog still `active`. Service now
survives dgmneto logging out instead of depending on an open ssh/vscode session.

## 2026-06-10 — Discovered + documented
Tracked down the "pause downloads while Plex streams" job the user remembered. It is a
`systemd --user` service (not cron), enabled + active on the server since 2026-04-29. Documented
mechanism (polls Plex `/status/sessions` every 5s, stops/starts qBittorrent torrents via `docker exec`,
resumes only self-paused hashes). Flagged two issues: `Linger=no` (dies if dgmneto's sessions all
close) and a hardcoded `QBITTORRENT_PASSWORD` default committed in `watchdog.py`. No change made.
