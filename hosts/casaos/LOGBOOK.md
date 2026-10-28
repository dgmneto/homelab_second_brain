# Logbook — casaos (host)

Reverse-chronological. Newest entry on top. Host-level changes on casaos: OS, disks, users, cron/timers.
See `../../LOGBOOK.md` for the project-wide log; service detail in `../../services/<svc>/LOGBOOK.md`.

## 2026-10-28 — Tailscale installed (native)
Added apt repo `pkgs.tailscale.com/stable/debian` bookworm + keyring, installed `tailscale` 1.104.4,
`tailscaled` enabled. New `/etc/sysctl.d/99-tailscale.conf` (`net.ipv4.ip_forward = 1`; IPv6 forwarding
intentionally not set). Subnet router for .11/.14/.15. Seen during `apt-get update`: 1Password repo key
expired (EXPKEYSIG) — not fixed. Verified containers/DNS/IPv6 routes unchanged. Detail:
`../../services/tailscale/LOGBOOK.md`.

## 2026-10-28 — Repo restructure: host folder created
Former `cron/` README + LOGBOOK moved here (`cron.md`, this file); casaos access, deployment
architecture and storage layout moved out of `CLAUDE.md` into `README.md`. No change on the server.
Earlier host-level history (disk rebuild 2026-08-08, 2026-08-03 hang) is in `../../LOGBOOK.md`.

## 2026-06-09 — Cron: documented all cron + timers
Probed `crontab -l`, root crontab, `/etc/crontab`, `/etc/cron.d`, `/etc/cron.*`, openclaw crontab, and
`systemctl list-timers`. Found two homelab-specific jobs: root weekly `backup.sh` (auto-push of the
deployment repo, Sun 05:00) and the openclaw daily chrome-debug band-aid (03:00, deletes wrong dir,
harmless). Rest is stock Debian/Google. No change made to any schedule.
