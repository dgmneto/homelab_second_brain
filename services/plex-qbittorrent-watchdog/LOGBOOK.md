# Logbook — plex-qbittorrent-watchdog

Reverse-chronological. Newest entry on top. See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-11 — Decommissioned (stopped + disabled)
User: "kill the qbittorrent watchdog, it isn't working properly". Found it active (PID 878 since
2026-09-15) but stuck: since 10:50 its state was `plex_streaming: true` with 7 `managed_hashes`,
journal showed only "Paused …" lines (no resume) for ~8h. Ran as claude via
`sudo -u dgmneto XDG_RUNTIME_DIR=/run/user/1002 systemctl --user disable --now plex-qbittorrent-watchdog.service`
→ `inactive`, unit symlink + `default.target.wants` link removed. Then resumed the 7 held hashes with
the watchdog's own `qbt_api_post(…start…)`: 4 back to `downloading`/`stalledUP` (Euphoria S01–S03,
The Furious), 3 no longer exist in qBittorrent. Code left in place in the deployment repo
(nothing to commit there — the installed unit was an out-of-repo symlink).

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
