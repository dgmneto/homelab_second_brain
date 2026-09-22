# Logbook — plex

Reverse-chronological. Newest entry on top. One entry per task that touches **plex** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-09-22 — Investigation: reported down, found up
Plex up 7d healthy; `/identity` 200 direct, via `filmin.3e` on LAN, and from the internet. Streamed
at 20:24. `filmin.intern.dgmneto.com` broken (no nginxIntern proxy host, TLS unrecognized name) but is
listed in Plex `customConnections`. Remote Access NAT-PMP fails ("Not Supported by gateway"),
state `Mapped - Not Published`, so remote clients rely on the `filmin.3e` custom URL.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
