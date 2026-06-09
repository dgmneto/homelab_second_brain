---
name: footage-disk-leak
description: Root cause + fix for recurring homelab outage where /footage fills to 100% and HA looks down
metadata:
  node_type: memory
  type: project
---

# /footage fills to 100% — recurring outage

Recurring "homeserver down" symptom: `/footage` (492G LVM volume) fills to 100%. Home Assistant's
config is bind-mounted there (`/footage/services/homeassistant/config`), so a full `/footage` makes HA
crash-loop on `OSError: [Errno 28] No space left on device` (can't write its startup lock) — that is
what looks like "down." Root disk `/` stays fine; check `df -h /footage` specifically.

**Root cause (fixed 2026-06-08):** the `openclaw` user had a systemd *user* unit
`~/.config/systemd/user/chrome.service` launching `google-chrome-stable --remote-debugging-port=9222`
with NO headless flag. On this headless box it died instantly (`Missing X server or $DISPLAY`), and
`Restart=on-failure RestartSec=5` respawned it every 5s — restart counter hit ~596,000. Each doomed
launch dropped a 4MB `BrowserMetrics-*.pma` into `~/.config/google-chrome/BrowserMetrics`, leaking
~429G (~110k files).

**Fix applied:** `systemctl --user disable --now chrome.service`, backed up the unit to
`~/chrome.service.removed.bak`, removed it, `daemon-reload`, cleared the `*.pma` files.
`openclaw-gateway.service` (the real service, node) has no dependency on it and was unaffected. A
useless crontab band-aid remains (`0 3 * * * rm -rf .../google-chrome-debug`) — it cleaned the wrong
dir; harmless now (see [../cron/README.md](../cron/README.md)).

If `/footage` fills again:
```
find ~openclaw/.config/google-chrome*/ -name '*.pma' -delete
```
and confirm `chrome.service` did not return. Access via [[ssh-access]].
