# Logbook — homelab (project-wide)

Reverse-chronological. Newest entry on top. One entry per task that touches the homelab — what
changed, why, commands run on the server, and the verified outcome. Per-service detail also goes in
the matching `services/<svc>/LOGBOOK.md`.

## 2026-08-06 — HDD replacement (in progress): Phase 0–1, `/library` shrunk, `sdb` evacuated
Replacing both failing disks (`notes/disk-health-storage-array.md`) with 2× 4TB, ending on an LVM
RAID1 mirror. Only 2 SATA ports exist and both were occupied, so the swap is a rolling one — no third
disk can ever be attached, and there is no USB dock.

**The trap this job exposed:** the volumes were only 22% full of data (805 GiB real) but **100%
allocated** (`VFree 0`), so `pvmove /dev/sdb` was impossible — it needed 1.82 TiB of free extents on
`sda` and there were none. `pvmove` moves *allocated extents*, not used blocks. The fix is to shrink
first. Second trap: `lvreduce` frees the LV's **highest** LEs, and `seg_pe_ranges` showed
`libraryLogicalVolume` was laid out **`sdb` first** (`sdb:0-476931`, then `sda:0-348931`) — so shrinking
freed the `sda` half, which is exactly what made room to then drain `sdb` onto `sda`. Always read
`lvs -o+seg_pe_ranges` before assuming which physical disk a shrink will empty.

Phase 0: verified extent map, `dm-raid` module present, `lvm2-monitor` enabled. Tarred
`/footage/services` (3.7G, 22,760 entries) to the Mac as a config safety net — note `/footage` is 44G
because Docker's **data-root is `/footage/docker`** (35G) plus the 18G `/footage/home/openclaw`
leftover, but the actual service configs are only 3.7G. Took everything down: all 20 containers +
`arani`, then `systemctl disable --now docker.socket docker.service containerd.service` — *disabling*
matters because restart policies plus watchtower's 30s poll would resurrect the stacks across the two
power-cycles this job needs. Also had to `systemctl --user stop plex-qbittorrent-watchdog.service`:
it is a `systemd --user` unit for `dgmneto` (as its README correctly says), so it survives
`compose down` and is invisible to system-scope `systemctl list-units`.

Phase 1: `umount /library` → `e2fsck -f -y` (clean; only extent-tree optimizations; 281 inodes,
213,028,448/845,684,736 blocks) → `resize2fs … 1000G` (~4 h, relocated ~560 GiB, no errors) →
`lvreduce -f -L 1000G` → `pvmove -i 60 /dev/sdb` (1000 GiB at ~133 MB/s, ~2.2 h) → `vgreduce` +
`pvremove /dev/sdb`. Long-running steps were launched `setsid nohup …` so they are PPID 1 and survive
SSH drops. Verified after: `pvs` shows only `/dev/sda` (`PFree <363.02g`), both LVs on `sda`,
`/library` mounts with 761G used / 178G free and `media/{movies,tv,transcoding}` + `torrent` intact,
`/footage` 41G. `lsblk` confirms `sdb` has no FSTYPE — safe to pull.

Progress helper installed at `/home/dgmneto/migration-progress.sh` (run via
`ssh -t dgmneto@homelab 'sudo /home/dgmneto/migration-progress.sh'`) — reports shrink / `pvmove` /
RAID1-sync progress, or dumps full volume state when nothing is running.

Next: physical swap of `sdb` (`WD2003FYYS-05T8B0`, `WD-WMAUR0541868`) → new disk N1, then Phase 2
drains `sda` onto N1, then `sda` (`WD20EZRX-00DC0B0`, `WD-WMC301625707`) → N2 and
`lvconvert --type raid1 -m1` on both LVs.

## 2026-08-03 — decommission openclaw (user no longer uses it)
User asked to remove `openclaw` (the AI agent gateway running as the `openclaw` Linux user, 4 Telegram
bot accounts: default/lobi/nutri/orion) completely. Did the reversible parts myself: `systemctl --user
stop` + `disable openclaw-gateway.service` (as `openclaw`, via `sudo -u openclaw`), backed up and
cleared its crontab (`0 3 * * * rm -rf .../google-chrome-debug`, the harmless band-aid from the
[[disk-health-storage-array]]-unrelated chrome.service leak — see `notes/footage-disk-leak.md`).
Per policy did **not** myself hard-delete data or 1Password items — left as commands/list for the user
to run: `/footage/home/openclaw` (18G) to remove, and four 1Password items (`OpenClaw Gateway Token`,
`OpenClaw Control`, `openClaw - Server Unix`, `OpenClaw - OpenRouter API key`, all in `Personal` vault)
to delete. Also flagged, not done: NPM proxy host for `openclaw` (192.168.11.13:18789) still needs
manual removal in nginxIntern's admin UI (see `ACCESS.md`); the 4 Telegram bot tokens still need
revoking via @BotFather; the `openclaw` Linux user account itself (uid 1009) still exists. `hermes` is
unaffected (separate service, only historically *read* openclaw's config once to seed its own
allowlist — no live dependency). Updated `notes/footage-disk-leak.md`, `services/homeassistant/README.md`,
and `ACCESS.md` to reflect the decommission. Verified: `systemctl --user status openclaw-gateway.service`
shows `disabled`/`inactive (dead)`, `crontab -l` for `openclaw` empty.

## 2026-08-03 — homelab down: disk-triggered 13-day hang + IP-collision fallout
User reported homelab down. `ping`/ARP to `192.168.11.13` showed the box fully unreachable at L2
(`incomplete` ARP entry, no route) — not an app/service issue, the host itself was wedged. User
physically checked and power-cycled it; `uptime` afterward confirmed a fresh boot. Root cause found
via `journalctl --list-boots` + `journalctl -b -1`: the previous boot's journal went silent at
`Jul 21 16:39:13` right after `smartd` logged pending sectors on **both** disks in the `library` LVM
array (`sda`: 1 pending, `sdb`: 2 pending + both show 1 offline-uncorrectable each) — 13 days of total
silence until the forced reboot. `smartctl` confirmed both disks: `sda` (WD Green, ~57,790 power-on
hrs) and `sdb` (WD RE4, ~127,584 hrs / ~14.6y old) are old and degrading, and the array has **no
RAID/mirror** (`libraryVirtualGroup` is linear/concatenated) — a bad-sector read almost certainly hung
the kernel/LVM I/O and froze the whole box. Documented in
[notes/disk-health-storage-array.md](notes/disk-health-storage-array.md) — open risk, no fix applied
yet (needs backup + eventual disk replacement/mirroring, flagged to user).

Post-reboot, two containers hadn't come back: `qbittorrent` (boot-order race with `gluetunProtonVPN`'s
network namespace, self-resolved on `docker compose up -d`) and `nginxProxyManagerProd` (stuck in
`Removal In Progress`, `failed to set up container networking: Address already in use` on its static
IP `172.21.0.9`). Second one was a real bug, unrelated to the disks: `hermes` has no static IP and had
been dynamically assigned `.9` on this boot. Fixed by pinning `hermes` to `172.21.0.250`
(`services/hermes/compose.yaml`), which freed `.9` for `nginxProd`. All 20 containers verified `Up`
(`docker ps -a`), `qbittorrent` and `plex`/`prowlarr`/`gluetunProtonVPN`/`watchtower` report `healthy`,
and `curl --resolve filmin.3e.dgmneto.com:443:192.168.14.33` returned `HTTP 401` (proxy alive). Detail
in [services/nginxProd/LOGBOOK.md](services/nginxProd/LOGBOOK.md) and
[services/hermes/LOGBOOK.md](services/hermes/LOGBOOK.md).

## 2026-07-04 — add Jellyfin alongside Plex
New media server, second player on the same `/library/media` library. Deployed
`ghcr.io/hotio/jellyfin:latest` under `/home/dgmneto/homelab/services/jellyfin/compose.yaml` on
`internalNetwork` only (no macvlan/static IP — simpler pattern than Plex, matches overseerr/bazarr),
`PUID=1005`/`PGID=1313` reused from `plex/.env` so file ownership matches, `/dev/dri` passed through
for HW transcode. Config dir `/footage/services/jellyfin/config` had to be `sudo mkdir`'d as `dgmneto`
— `/footage/services` is root-owned and `openclaw` (the compose file's documented "deployment user")
turned out to have neither passwordless sudo nor read access there; corrected that stale claim in
`CLAUDE.md`. Added reverse-proxy hosts in both NPM instances: `jellyfin.intern.dgmneto.com` (nginxIntern,
reused `*.intern.dgmneto.com` cert) and `jellyfin.3e.dgmneto.com` (nginxProd, reused `*.3e.dgmneto.com`
cert), both Force SSL + Websockets Support on. User completed the first-run setup wizard and confirmed
both URLs load and libraries are scanning. Verified: `docker compose ps` shows `Up`, GPU device log line
confirms `renderD128` picked up, both hostnames render Jellyfin UI in browser (internal already logged
in and scanning; public shows login page). See [services/jellyfin/README.md](services/jellyfin/README.md).

## 2026-07-04 — server health deep-check (investigation only)
Full pass: `uptime`, `df -h` (/, /footage, /library), `free -h`, `docker ps`, `docker stats`,
restart counts, inode usage, `dmesg`/`journalctl -k` OOM grep, `journalctl -u docker -p err`,
gluetun + watchtower logs, z2mqtt log, host `ps aux --sort=-%mem`. All 20 containers up, no
crash-loops, 0 OOM kills in 7d, 0 docker daemon errors in 7d. Disk healthy: `/` 53%,
`/footage` 9%, `/library` 65%, inodes all <10%. Mem: 4.3Gi/7.6Gi used, 656Mi swap in use but
3.3Gi available (buff/cache reclaimable) — not concerning. z2mqtt RestartCount=1 traced to the
2026-06-28 watchtower weekly run recreating it (not a crash — log has no errors). Watchtower's
last run (2026-06-28 10:08 UTC, per the new Sunday-10:00 cron from commit 9d35b56) updated 10 of
20 containers with 0 failures. Gluetun port-forwarding had one transient retry then succeeded —
normal. No action taken; server is healthy.

## 2026-06-22 — prowlarr: move off VPN to internalNetwork
Prowlarr was routing indexer traffic through ProtonVPN (gluetun netns). VPN exit IPs were blocking tracker domains. Zen Internet (UK ISP) does minimal voluntary blocking so VPN is unnecessary for HTTP indexer queries. Moved prowlarr to `internalNetwork` directly; updated NPM proxy host to forward to `prowlarr:9696` instead of `gluetun:9696`. Verified reachable at `prowlarr.intern.dgmneto.com`.
Detail: [services/prowlarr/LOGBOOK.md](services/prowlarr/LOGBOOK.md).

## 2026-06-22 — hermes: add read-only Docker access via socket proxy
Added `tecnativa/docker-socket-proxy` sidecar to hermes compose. Hermes reads Docker API
(containers, images, networks, volumes, info) via `tcp://hermes-docker-proxy:2375` — no write
or exec endpoints exposed. Both containers up and healthy.
Detail: [services/hermes/LOGBOOK.md](services/hermes/LOGBOOK.md).

## 2026-06-22 — watchtower: switch from 30s interval to weekly cron
Hermes gateway was restarting constantly (26+ times on 2026-06-21). Root cause: upstream
`nousresearch/hermes-agent:latest` publishes new images every ~10 minutes during active dev;
watchtower at `--interval 30` picked up every one. Changed watchtower schedule to
`--schedule "0 0 10 * * 0"` (Sundays 10:00 UTC) across all containers. Next update:
2026-06-28. Detail: [services/watchtower/LOGBOOK.md](services/watchtower/LOGBOOK.md).

## 2026-06-15 — New service: Hermes AI agent (Telegram + OpenRouter)
Deployed `nousresearch/hermes-agent` as a new compose service on the server
(`/home/dgmneto/homelab/services/hermes/`), config at `/footage/services/hermes/config`. Wired
Telegram bot (new token) + dedicated OpenRouter key (both stored in 1Password Personal). Telegram
allowlist (2 users + 2 groups) copied from the existing `openclaw` agent's config. Isolation via
container hardening only (no new Linux user) — see `services/hermes/README.md` and
`services/hermes/LOGBOOK.md` for full detail. Verified: telegram connected, ~180MB/2GB RAM idle.

## 2026-06-15 — arr-stale-cleaner fix: dead no-metadata torrents weren't cleaned
One-week review of the arr-maintenance crons. Both ran clean every 6h for 5 days (no
failures). But the stale-cleaner left ~18 Sonarr queue items stuck the whole week, logged
as "complete, import pending". Turned out they were `metaDL`/`queuedDL` torrents that never
fetched metadata (`size=0, progress=0, amount_left=0`) — dead releases the profile
downgrades grabbed, not completed downloads. Two v1 bugs fixed: (1) completion judged by
`progress>=1`/`completion_on>0` instead of `amount_left==0`; (2) `idle_seconds()` falls
back to `added_on` when qBit's `last_activity` is a never-started sentinel (was producing
negative idle, so stalls never flagged). Live run cleaned 18 (remove+blocklist+re-search),
queue 19→1; re-searches grabbed different releases. Touched sonarr, qbittorrent. Detail:
[services/arr-maintenance/LOGBOOK.md](services/arr-maintenance/LOGBOOK.md).

## 2026-06-10 — New service arr-maintenance: quality-fixer + stale-cleaner
Built two host cron jobs (deployment repo `services/arr-maintenance/`, Python3 stdlib,
shared `arr_common.py`) to keep the arr pipeline unstuck. API keys read from each
`config.xml` at runtime; logs beside the scripts.

**arr-quality-fixer** (daily `0 2 * * *`): for monitored, file-less, released/aired items
NOT in the download queue — <48h since added (or aired/released) → search; >=48h → set
restrictive profile (SD/720p/UHD) to HD-1080p(4) then search. Sonarr per-episode search
(batched per series) + per-series profile change; Radarr per-movie. First live run: 3
Sonarr series + 1 Radarr movie downgraded off Ultra-HD, 42 ep + 1 movie searches, 1
unreleased skipped (exit 0).

**arr-stale-cleaner** (every 6h `0 */6 * * *`): for each Sonarr/Radarr queue item still
downloading, match its torrent in qBittorrent by hash; `now - last_activity > 36h` →
remove from queue (`removeFromClient&blocklist&skipRedownload`) + re-search. qBit reached
via `docker exec qbittorrent curl localhost:9090` (localhost auth-bypass, no creds; rides
gluetun ns, no host port). First live run removed 2 stalls (Hacks S01E02/E03, 214.7h idle),
blocklisted + re-searched (exit 0).

Overlap: quality-fixer skips anything already in the download queue (won't downgrade/search
an active grab). Full runbook:
[services/arr-maintenance/README.md](services/arr-maintenance/README.md). Touched sonarr,
radarr (profiles + searches), qbittorrent (stale torrents removed).

## 2026-06-10 — Symlinked harness memory dir to repo `notes/`
Made `notes/` the actual auto-memory store: gave each note harness frontmatter + a `notes/MEMORY.md`
index, then symlinked the harness path
(`~/.claude/projects/-Users-dgmneto-homelab/memory` → `/Users/dgmneto/homelab/notes`). Auto-recall now
reads the real repo files and new memories land in-repo. Old memory dir backed up to `memory.bak.<ts>`.
Symlink is Mac-local/per-machine (not in git) — recreate steps in `notes/README.md`.

## 2026-06-10 — Migrated agent memory into repo `notes/`
Moved the three `~/.claude` project memories (ssh-access, footage-disk-leak, qbittorrent-mass-stop)
into version-controlled `notes/` with a `notes/README.md` index; CLAUDE.md now points there and names
`notes/` the home for durable cross-cutting facts. Reduced the external memory files to recall pointers
(the harness memory dir is a fixed path, can't be relocated — but the repo is now the single source of
truth and the pointers route agents here).

## 2026-06-10 — Added self-improvement mandate to CLAUDE.md
Added a top-of-file "this repo is built for agents to improve" section: every agent must correct stale
docs in the same task, capture mistaken assumptions where the next agent will hit them, restructure
freely, and prefer durable root-cause fixes over perpetual warnings.

## 2026-06-10 — Investigated "all qBittorrent downloads paused"
Drove WebUI via Claude-in-Chrome: all 28 torrents `Stopped`/0 B/0%, but VPN+disk+config
all healthy (green connectivity, 889 GiB free, auto-start OFF). Root cause: `watchtower`
auto-updated the unpinned qbit `:latest` (build-date 2026-06-08), recreated the
container, torrents came back stopped. No state change made. Added a stopped-downloads
decision-table runbook to `services/qbittorrent/README.md`. See its LOGBOOK for detail.

## 2026-06-10 — Split access docs to per-service ACCESS.md
Moved per-service access detail (URL, `op://` credential, auth method, quirks) out of the root
`ACCESS.md` into `services/<svc>/ACCESS.md` for 11 UI services (overseerr, plex, sonarr, radarr,
prowlarr, bazarr, qbittorrent, homeassistant, z2mqtt, nginxIntern, nginxProd). Root `ACCESS.md` is now
an index + shared vault/Chrome notes.

## 2026-06-10 — Overseerr login tested via Chrome tab
Drove the Claude-on-Chrome tab to `overseerr.intern.dgmneto.com`: reachable, renders the sign-in page
with "Use your Plex account" (OAuth) and "Use your Overseerr account" (local) buttons — not currently
authenticated. Did not complete login: entering credentials to authenticate is out of scope (user
performs it). Confirms the Chrome-tab access path works end to end up to the auth boundary.

## 2026-06-10 — Vault UI logins added; verified op access
User moved credentials into the `Homelab` vault — now 11 items, including LOGIN entries for qbittorrent,
Sonarr, Radarr, Prowlarr, Plex, nginx (intern NPM), NGINX Prod. Verified `op` can read them (usernames +
password fields present; values not revealed). Updated `ACCESS.md` to reference `op://Homelab/<item>`
per service. Still missing: Bazarr, HA, Zigbee2MQTT. qBittorrent pw now in vault but still hardcoded in
watchdog.py — flagged to reconcile.

## 2026-06-10 — Service access map (URLs ↔ credential source)
Asked to log into Overseerr using a password from `op`. Not possible: Overseerr uses Sign-in-with-Plex
OAuth and the `Homelab` vault has only 4 infra secrets (no app-UI logins). Also did not perform the
login (interactive password auth is out of scope). Instead pulled the authoritative proxy hostnames
from both NPM sqlite DBs and wrote `ACCESS.md` mapping each service URL to where its credential actually
lives, flagging that op holds no UI passwords (and qBittorrent's is hardcoded in watchdog.py).

## 2026-06-10 — Documented Chrome-extension UI access
Verified service web UIs are reachable through the Claude-in-Chrome extension driving the user's local
Chrome (loaded `overseerr.intern.dgmneto.com/login` successfully). Documented the access flow and the
NPM hostname scheme (`<svc>.intern.dgmneto.com` internal, public via nginxProd) in `CLAUDE.md`.

## 2026-06-10 — Enabled linger for dgmneto
Ran `loginctl enable-linger dgmneto` so the `plex-qbittorrent-watchdog` user service survives logout
(was `Linger=no`, only alive via open sessions). Now `Linger=yes`, service still active. Server change.

## 2026-06-10 — Tested `op` CLI, documented secret access
Verified the 1Password `op` CLI (v2.30.3) works via desktop-app integration (no manual signin).
Confirmed `op vault list` / `op item list` / search against the `Homelab` vault. Added a "Secrets"
section to `CLAUDE.md` with access/search commands and a no-secrets-in-repo rule. Did not extract any
secret values (classifier blocked a test read; not needed). Noted there is no qBittorrent item in the
vault yet.

## 2026-06-10 — Found the Plex→qBittorrent pause job
The "pause downloads while Plex streams" job the user remembered is **not cron** — it is the
`plex-qbittorrent-watchdog` `systemd --user` service (active since 2026-04-29). Documented it under
`services/plex-qbittorrent-watchdog/`, cross-linked from plex/qbittorrent READMEs and the cron note.
Flagged a leaked hardcoded `QBITTORRENT_PASSWORD` in the deployment repo's `watchdog.py` and the
`Linger=no` fragility. No server change.

## 2026-06-09 — Documented cron jobs + commit/push rule
Added the "commit and push ASAP" rule to `CLAUDE.md`. Probed all scheduled jobs on the server and
documented them under `cron/` (README + LOGBOOK). Homelab-specific: root weekly `backup.sh`
(auto-push of deployment repo, Sun 05:00) and openclaw chrome-debug band-aid (daily 03:00, harmless).
No server state changed.

## 2026-06-09 — Hello World
Logbook initiated. Knowledge base scaffolded: root `CLAUDE.md`, `services/<svc>/README.md` for all
18 services, and logbooks (root + per service). No server state changed.
