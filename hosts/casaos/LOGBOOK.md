# Logbook — casaos (host)

Reverse-chronological. Newest entry on top. Host-level changes on casaos: OS, disks, users, cron/timers.
See `../../LOGBOOK.md` for the project-wide log; service detail in `../../services/<svc>/LOGBOOK.md`.

## 2026-11-18 — Pushed casaos compose repo to GitHub from a cloud session
User approved attaching `dgmneto/homelab` with push access. Cloned it here (GitHub `main` = `4c396c1` = casaos `origin/main`), bundled
casaos's `origin/main..main` (10 commits, `64886b3`…`06f846e`) over ssh, fast-forwarded, checked the diff for literal secrets (none;
OPENROUTER key / terminus passwords come from env/gitignored `.env`), pushed: `4c396c1..06f846e`. On casaos, `update-ref
refs/remotes/origin/main 06f846e` → `git status` = `main...origin/main` (in sync). The recipe is now in the casaos README, and CLAUDE.md
points to it; MIGRATION.md's "local only" note for `511e3d6` is corrected.

## 2026-11-16 — Compose repo: committed live prowlarr/watchtower/hermes config (push pending from Mac)
`/home/dgmneto/homelab` had uncommitted `services/prowlarr/compose.yaml` (internalNetwork) and `services/watchtower/compose.yaml`
(`--schedule "0 0 10 * * 0"`) plus an untracked `services/hermes/` (hermes + hermes-docker-proxy, both stopped for about 5 weeks). All three
match the running containers, so they were committed as dgmneto. `main` is now **ahead of origin by 10** (d32bd32 and earlier, plus this one):
run `git push` in `~/homelab` on casaos from the Mac (casaos has no GitHub key).

## 2026-11-16 — Rack case designed (10" 3U, ZimaBoard + HBA + 4 x 3.5")
Read the hardware over Tailscale SSH (`claude@casaos`). `dmidecode` reports a ZimaBoard 832. `lspci` shows only the onboard
Intel AHCI controller, so no HBA is installed yet. `lsblk`/`smartctl` show sda HGST HUS724040ALA640 and sdb Toshiba MG08ADA400E,
both 3.5" 7200 rpm, plus the eMMC. Designed a printable 3U case for the Lab Rax rack: a column with a Flex-ATX PSU, the ZimaBoard
and the HBA on removable shelves, and a cage with 4 x 3.5" slots behind a 120 mm fan. `hardware/case/build_case.py` uses manifold3d, not Blender.
`render.mjs` renders through Playwright + three.js. `build_case.py` checks clearances and the assembly paths: OK. All STLs are manifold
(status NoError). Unverified dimensions are listed in the case README. The notebook's rear brackets are reused. Nothing printed or bought.

## 2026-11-15 — Investigation: can any host run a Satisfactory dedicated server?
Read-only. `ssh casaos` → `lscpu`/`free`/`dmidecode`/`docker stats`: Celeron N3450 4c, 7.6 GiB (max 8 GB), load ~5, swap in use.
homelab-notebook per README: Celeron N4020 2c, 11.7 GB (HA stack uses ~2 GB), 5400 rpm HDD. Verdict: neither is adequate
(game server wants ~12–16 GB RAM + strong single-thread CPU); casaos hardware added to its README.

## 2026-11-11 — Removed dgmneto user unit plex-qbittorrent-watchdog
`systemctl --user disable --now` (run as claude via `sudo -u dgmneto XDG_RUNTIME_DIR=/run/user/1002`).
Unit now absent from dgmneto's user manager. Linger for dgmneto left on (harmless).

## 2026-11-02 — terminus-worker joined internalNetwork (172.21.0.142)
Compose change in `~/homelab/services/terminus` (committed on casaos, push from Mac). See services/terminus.

## 2026-11-01 — Removed backup.sh cron + script
Root crontab line `0 5 * * 0 cd /home/dgmneto/homelab && ./services/backup.sh` removed (backup `/root/crontab.bak-20261101`); script
`git rm`'d (29f0fef). Root crontab now empty.

## 2026-11-01 — Retired compose stacks moved to deprecated/
`/home/dgmneto/homelab`: `git mv services/{homeassistant,z2mqtt,mosquitto,matter} deprecated/` + `deprecated/README.md`
(do-not-up warning), committed as dgmneto (c1633a0; pushed by Sunday backup.sh).

## 2026-10-31 — HA migration Phase 4 (Home Assistant → homelab-notebook)
Home-automation stack fully off casaos: `docker compose down` for mosquitto (10-30), z2mqtt (10-30), matter-server (10-30), homeassistant (10-31). Data dirs under `/footage/services/` kept; HA `configuration.yaml` got a `.bak-pre-move` copy plus the 192.168.11.13 trusted_proxies line.

## 2026-10-30 — Added `nbbackup` user + backup-prune cron (homelab-notebook backups)
`useradd --system --home-dir /footage/backups/homelab-notebook --shell /bin/sh nbbackup` (uid 998);
`/footage/backups{,/homelab-notebook{,/.ssh}}` 0700 nbbackup; authorized_keys = laptop key with
`command="/usr/bin/rrsync -wo /footage/backups/homelab-notebook",restrict,from="192.168.11.21"`.
`/etc/cron.d/homelab-notebook-backup`: 05:41 daily, delete `history/*` dirs older than 14 days. Verified from the
laptop: write OK (+ history copy), read/escape/shell refused; test files removed afterwards.

## 2026-10-28 — Removed stale sudoers drop-in `migration-task2`
`/etc/sudoers.d/migration-task2` (Apr 29, leftover from an old migration per user) gave dgmneto NOPASSWD
for rsync/mkdir/mv/rm/sed/usermod/find/crontab — near-root. Checked nothing used it first: no crontab
or systemd unit mentions sudo, no script under ~/homelab or /usr/local/bin calls those via sudo, auth
log shows no NOPASSWD use. `sudo rm` it (as `claude`), `visudo -c` OK, `sudo -l -U dgmneto` → only
`(ALL : ALL) ALL` (password required).

## 2026-10-28 — Cloud sessions log in to casaos as `claude` (passwordless sudo)
User switched the tailnet ssh rule for `tag:claude` to `users: ["claude"]`. Verified from a cloud session:
`ssh claude@casaos` → uid 1306, groups claude+docker, `sudo -n true` OK; `ssh dgmneto@casaos` now refused
by policy. Hook ssh config changed to `User claude` for casaos/homelab. Read
`/etc/sudoers.d/migration-task2`: dgmneto NOPASSWD for rsync/mkdir/mv/rm/sed/usermod/find/crontab.

## 2026-10-28 — `claude` user with passwordless sudo
`useradd -m -s /bin/bash -G docker claude`; `/etc/sudoers.d/90-claude` = `claude ALL=(ALL) NOPASSWD: ALL`
(0440), `visudo -c` parsed OK. Run by user via sudo in terminal. Verified `id claude` → uid 1306,
groups claude+docker. No SSH key / password set yet — login method pending.

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
