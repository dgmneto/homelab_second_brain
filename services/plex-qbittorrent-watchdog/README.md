# plex-qbittorrent-watchdog

> **⛔ DECOMMISSIONED 2026-11-11** — stopped + disabled at the user's request ("isn't working
> properly"). Nothing pauses qBittorrent during Plex playback any more. The code still sits in the
> deployment repo (`/home/dgmneto/homelab/services/plex-qbittorrent-watchdog/`) but the unit is
> **not installed**: `systemctl --user disable` removed the `~/.config/systemd/user/` symlink, so
> `systemctl --user status` now says "could not be found" — that is expected, not a bug.
> **Failure seen:** from 10:50 on 2026-11-11 it believed Plex was streaming non-stop (no "Resumed"
> for ~8h, repeated "Paused" lines) and held 7 torrents stopped; its plex-session detection
> (`plex_has_active_streams`) apparently kept seeing a stale/idle session as active.
> Everything below is historical. To revive: fix detection first, then
> `systemctl --user link <repo>/plex-qbittorrent-watchdog.service && systemctl --user enable --now …`.

Pauses qBittorrent transfers while anyone is streaming on Plex, then resumes **only** the torrents it
paused once Plex goes idle. Keeps streams from competing with downloads for bandwidth/disk.

**This is NOT a cron job** — it is a long-running `systemd --user` service for the `dgmneto` user.
That is why it does not appear in any crontab or in system `systemctl`. (The user originally
remembered it as a cron job; it isn't.)

## Where it lives
- Code + unit on the server (deployment repo `dgmneto/homelab`):
  `/home/dgmneto/homelab/services/plex-qbittorrent-watchdog/`
  - `watchdog.py` — the poller/controller
  - `plex-qbittorrent-watchdog.service` — the systemd --user unit
  - `tests/test_watchdog.py`, `TECHNICAL_DETAILS.md`, `README.md`
- Installed as: `~/.config/systemd/user/plex-qbittorrent-watchdog.service` (symlink).

## How it works
- Polls Plex **every 5s**: `docker exec plex curl "http://127.0.0.1:32400/status/sessions?X-Plex-Token=…"`.
- ≥1 active Plex session → logs into qBittorrent (`docker exec qbittorrent curl .../api/v2/auth/login`),
  calls the qBittorrent 5.x **`stop`** endpoint on currently-active torrents, and records the hashes it
  stopped in its state file.
- Plex idle again → calls **`start`** for **only** the hashes it previously stopped (torrents you
  paused manually stay paused). State persisted in `%t/plex-qbittorrent-watchdog/state.json`
  (i.e. `/run/user/<uid>/…`).
- Talks to both containers via `docker exec` (Plex on `:32400`, qBittorrent on `:9090` inside the
  gluetun namespace), so it needs Docker access and runs on the host, not in a container.

## Config (env vars, with defaults in watchdog.py)
`PLEX_CONTAINER=plex`, `QBITTORRENT_CONTAINER=qbittorrent`, `QBITTORRENT_USERNAME=admin`,
`QBITTORRENT_PASSWORD=<set>`, `POLL_INTERVAL_SECONDS=5`, `STATE_FILE`. The unit overrides with
`--poll-interval 5 --state-file %t/plex-qbittorrent-watchdog/state.json`.

## Manage / debug (historical — unit no longer installed)
From a cloud session (`ssh casaos` as `claude`) target dgmneto's user manager with
`sudo -u dgmneto XDG_RUNTIME_DIR=/run/user/$(id -u dgmneto) systemctl --user …`; the code dir is
`dgmneto`-only (0700-ish), so `cd`/`grep` it via `sudo`.
```
systemctl --user status plex-qbittorrent-watchdog.service
journalctl --user -u plex-qbittorrent-watchdog.service -f
python3 ~/homelab/services/plex-qbittorrent-watchdog/watchdog.py --once   # single check
```

## Quirks / runbook
- **Status (2026-11-11): decommissioned** (see top). Previously (2026-06-10): enabled + active, running since 2026-04-29 (~1mo, ~20h CPU). Healthy.
- **Linger enabled (2026-06-10):** `loginctl enable-linger dgmneto` was run (marker
  `/var/lib/systemd/linger/dgmneto`), so the user manager — and this service — now survives dgmneto
  logging out. Previously `Linger=no` and it only stayed up because a session was always open.
  Verify with `loginctl show-user dgmneto -p Linger` (expect `Linger=yes`).
- **⚠️ Hardcoded credential:** `watchdog.py` ships a default `QBITTORRENT_PASSWORD` value in source,
  committed to the `dgmneto/homelab` repo. That is a leaked qBittorrent password — rotate it and read
  it from env/secret instead of a literal default. Not reproduced in this repo on purpose.
- Depends on Plex AND qBittorrent containers being up; qBittorrent rides the gluetun VPN namespace
  (see `../qbittorrent/README.md`), so its `:9090` is reachable from the host via `docker exec`.

Related: `../plex/README.md`, `../qbittorrent/README.md`.
