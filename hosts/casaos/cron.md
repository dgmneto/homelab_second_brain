# Cron / scheduled jobs

Scheduled jobs on the homelab server (`dgmneto@homelab`, Debian 12). Covers cron + systemd timers.
Probe sources: `crontab -l`, `sudo crontab -l`, `/etc/crontab`, `/etc/cron.d`, `/etc/cron.{hourly,daily,weekly,monthly}`, `systemctl list-timers --all`.

## Homelab-specific jobs (the ones that matter)

### `/etc/cron.d/homelab-notebook-backup` — prune laptop backup history (added 2026-10-30)
```
41 5 * * * root find /footage/backups/homelab-notebook/history -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +
```
Keeps 14 days of `history/` for the nightly push from homelab-notebook (see
[MIGRATION.md § Backups](../../services/homeassistant/MIGRATION.md#backups-live-since-2026-10-30)).

### ~~root crontab — weekly deployment-repo backup~~ (REMOVED 2026-11-01)
`0 5 * * 0 cd /home/dgmneto/homelab && ./services/backup.sh` and the script itself were deleted at the user's request
(root crontab backup: `/root/crontab.bak-20261101`; script removal = server-repo commit 29f0fef). It had never worked since
2025-04: root vs dgmneto-owned repo → git "dubious ownership"; `~/.ssh/github_ed25519` passphrase-protected (noted 2026-08-08);
and GitHub rejects both on-box keys anyway. **Root's crontab is now empty.** The compose repo `/home/dgmneto/homelab` is
only backed up when someone commits **and pushes by hand** (from the Mac; casaos has no working GitHub key).

### openclaw user crontab — chrome-debug cleanup (band-aid, harmless)
```
0 3 * * *  rm -rf /footage/home/openclaw/.config/google-chrome-debug
```
Daily 03:00. Leftover band-aid from the old `/footage`-fill incident. It deletes the **wrong**
directory — the actual leak was `*.pma` files under `~openclaw/.config/google-chrome/BrowserMetrics`
from a crash-looping `chrome.service` (now removed). Harmless but useless; safe to delete.
See `../../services/homeassistant/LOGBOOK.md` and the `homelab-footage-chrome-leak` memory.

### dgmneto crontab — arr-maintenance jobs
`arr-stale-cleaner` (every 6h) and `arr-quality-fixer` (nightly) — see
[../../services/arr-maintenance/README.md](../../services/arr-maintenance/README.md) for schedule and runbook.

## Not cron, but commonly mistaken for it
- **plex-qbittorrent-watchdog** — pauses qBittorrent while Plex streams. It is a long-running
  `systemd --user` service for `dgmneto`, **not** a cron job, so it appears in neither crontabs nor
  system `systemctl`. Check with `systemctl --user status plex-qbittorrent-watchdog`. See
  `../../services/plex-qbittorrent-watchdog/README.md`.

## Stock Debian / vendor jobs (not homelab-specific, listed for completeness)

- `/etc/crontab`: standard `run-parts` for `cron.hourly|daily|weekly|monthly` (Debian default).
- `/etc/cron.daily/`: `0anacron apt-compat dpkg google-chrome logrotate man-db samba`.
  `google-chrome` = Google's apt-repo/keyring refresh (installed by Chrome package; unrelated to the
  leak incident, which was a systemd user unit).
- `/etc/cron.d/`: `anacron`, `e2scrub_all` (LVM fsck scrub).
- **systemd timers** (`systemctl list-timers`): `apt-daily`, `apt-daily-upgrade`, `logrotate`,
  `dpkg-db-backup`, `man-db`, `anacron`, `systemd-tmpfiles-clean`, `e2scrub_all`, `fstrim`. All stock.

## Re-checking cron
```
ssh dgmneto@homelab 'sudo crontab -l; for u in openclaw; do sudo crontab -l -u $u; done; \
  cat /etc/crontab; ls /etc/cron.d /etc/cron.daily; systemctl list-timers --all --no-pager'
```
(Reading the openclaw crontab needs root — `sudo crontab -l -u openclaw` — or SSH as openclaw.)
