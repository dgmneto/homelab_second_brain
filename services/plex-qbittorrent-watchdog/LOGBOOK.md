# Logbook — plex-qbittorrent-watchdog

Reverse-chronological. Newest entry on top. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-10 — Discovered + documented
Tracked down the "pause downloads while Plex streams" job the user remembered. It is a
`systemd --user` service (not cron), enabled + active on the server since 2026-04-29. Documented
mechanism (polls Plex `/status/sessions` every 5s, stops/starts qBittorrent torrents via `docker exec`,
resumes only self-paused hashes). Flagged two issues: `Linger=no` (dies if dgmneto's sessions all
close) and a hardcoded `QBITTORRENT_PASSWORD` default committed in `watchdog.py`. No change made.
