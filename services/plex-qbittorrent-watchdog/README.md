# plex-qbittorrent-watchdog

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

## Manage / debug
```
systemctl --user status plex-qbittorrent-watchdog.service
journalctl --user -u plex-qbittorrent-watchdog.service -f
python3 ~/homelab/services/plex-qbittorrent-watchdog/watchdog.py --once   # single check
```

## Quirks / runbook
- **Status (2026-06-10):** enabled + active, running since 2026-04-29 (~1mo, ~20h CPU). Healthy.
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
