# Cron / scheduled jobs

Scheduled jobs on the homelab server (`dgmneto@homelab`, Debian 12). Covers cron + systemd timers.
Probe sources: `crontab -l`, `sudo crontab -l`, `/etc/crontab`, `/etc/cron.d`, `/etc/cron.{hourly,daily,weekly,monthly}`, `systemctl list-timers --all`.

## Homelab-specific jobs (the ones that matter)

### root crontab — weekly deployment-repo backup
```
0 5 * * 0  cd /home/dgmneto/homelab && ./services/backup.sh
```
Sundays 05:00. Runs `/home/dgmneto/homelab/services/backup.sh`, which auto-commits and pushes the
**deployment** compose repo (`/home/dgmneto/homelab` → `git@github.com:dgmneto/homelab.git`):
```bash
#!/bin/bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_ed25519
git add .
git commit -m 'auto-backup'
git push -u origin main
```
Notes / quirks:
- This backs up the **server's compose repo**, NOT this second-brain repo.
- No error handling: if `git commit` finds nothing staged it exits non-zero, but the script ignores
  it. Push uses `~/.ssh/github_ed25519` (separate from the on-disk `id_rsa`).
- Commit message is always `auto-backup` — no diff detail.

### openclaw user crontab — chrome-debug cleanup (band-aid, harmless)
```
0 3 * * *  rm -rf /footage/home/openclaw/.config/google-chrome-debug
```
Daily 03:00. Leftover band-aid from the old `/footage`-fill incident. It deletes the **wrong**
directory — the actual leak was `*.pma` files under `~openclaw/.config/google-chrome/BrowserMetrics`
from a crash-looping `chrome.service` (now removed). Harmless but useless; safe to delete.
See `../services/homeassistant/LOGBOOK.md` and the `homelab-footage-chrome-leak` memory.

## Not cron, but commonly mistaken for it
- **plex-qbittorrent-watchdog** — pauses qBittorrent while Plex streams. It is a long-running
  `systemd --user` service for `dgmneto`, **not** a cron job, so it appears in neither crontabs nor
  system `systemctl`. Check with `systemctl --user status plex-qbittorrent-watchdog`. See
  `../services/plex-qbittorrent-watchdog/README.md`.

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
