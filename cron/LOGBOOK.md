# Logbook — cron

Reverse-chronological. Newest entry on top. One entry per task touching scheduled jobs on the server.
See `../LOGBOOK.md` for the project-wide log.

## 2026-06-09 — Documented all cron + timers
Probed `crontab -l`, root crontab, `/etc/crontab`, `/etc/cron.d`, `/etc/cron.*`, openclaw crontab, and
`systemctl list-timers`. Found two homelab-specific jobs: root weekly `backup.sh` (auto-push of the
deployment repo, Sun 05:00) and the openclaw daily chrome-debug band-aid (03:00, deletes wrong dir,
harmless). Rest is stock Debian/Google. No change made to any schedule.
