---
name: qbittorrent-mass-stop
description: qBittorrent "all downloads paused" is usually a watchtower restart, not VPN/disk; how to diagnose via Chrome
metadata:
  node_type: memory
  type: project
---

# "All downloads paused" — usually a watchtower restart

When the user reports "all my downloads are paused," the cause is usually **not** VPN or disk. Most
common: `watchtower` auto-updated qBittorrent's unpinned `:latest` image (30s poll) and recreated the
container — torrents come back in `Stopped` state (all of them, 0 B, 0.0%) and nobody resumes them.
Confirm with `docker logs qbittorrent | head` → `Build-date:`.

Diagnose by **opening the WebUI via Claude-in-Chrome first** (faster than server logs — state is
visible instantly): `https://qbittorrent.intern.dgmneto.com`, no login (NPM-only). `read_page`
overflows the 50k limit there — use a `computer` screenshot. Bottom status bar: **green globe** =
VPN/peers OK, blue speed-limiter = no throttle, "Free space" = disk OK.

Two other pause causes: the **plex-qbittorrent-watchdog** (stops *active* torrents during Plex
playback — won't touch never-started 0 B torrents), and config auto-pause (Tools → Options →
Downloads, currently OFF). Full decision-table runbook lives in
[../services/qbittorrent/README.md](../services/qbittorrent/README.md).

Related: [[footage-disk-leak]], [[ssh-access]].
