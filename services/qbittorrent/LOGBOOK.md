# Logbook — qbittorrent

Reverse-chronological. Newest entry on top. One entry per task that touches **qbittorrent** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-06-10 — Diagnosed "all downloads paused"; added stopped-downloads runbook
User reported all downloads paused. Opened WebUI via Claude-in-Chrome
(`qbittorrent.intern.dgmneto.com`, no login). Found all **28 torrents `Stopped`, 0 B,
0.0%**; status bar **green globe** (VPN/peers OK), blue speed-limiter (no throttle),
889 GiB free, DHT ~366 nodes. gluetun/qbit/prowlarr all `Up 24h (healthy)`; disk
9%/71%. Tools→Options→Downloads "Do not start automatically"=OFF, stop condition=None
— so not a config auto-pause. Conclusion: **mass stop after a `watchtower` auto-update**
(qbit image `Build-date 2026-06-08`, unpinned `:latest`) recreated the container and
torrents returned `Stopped`; watchdog ruled out (only stops *active* torrents, these
were 0 B/never-started). No change made to running service (user not yet asked to
resume). Added a "downloads all paused/stopped" decision-table runbook to `README.md`.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
