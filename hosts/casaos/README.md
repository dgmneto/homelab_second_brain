# casaos — main homelab server (Docker)

`192.168.11.13`, hostname `casaos`, SSH alias `homelab`. **x86_64 Debian 12 (bookworm)** — older notes
calling it a Raspberry Pi are wrong. Runs every Docker service in [../../services/](../../services/)
except [hermes](../../services/hermes/README.md) (moved to [homelab-notebook](../homelab-notebook/README.md)).

Also here: [cron.md](cron.md) (crontabs + systemd timers), [LOGBOOK.md](LOGBOOK.md) (host-level
changes: OS, disks, users, cron). Cross-cutting memories about this box live in
[../../notes/](../../notes/) (that folder is the harness auto-memory symlink, so it stays at the root):
[ssh-access](../../notes/ssh-access.md), [footage-disk-leak](../../notes/footage-disk-leak.md),
[disk-health-storage-array](../../notes/disk-health-storage-array.md).

## Access

The homelab is `homelab` (`192.168.11.13`, hostname `casaos`), an **x86_64 Debian 12 (bookworm)**
box. (Older notes call it a Raspberry Pi — that is wrong; it is x86_64.)

```
ssh dgmneto@homelab
```

If the 1Password SSH agent is locked/dead, key signing fails (`Permission denied (publickey)`).
Bypass the agent and use the key file directly:

```
ssh -o IdentityAgent=none -o IdentitiesOnly=yes -i ~/.ssh/id_rsa dgmneto@homelab
```

For the deployment user add `-o User=openclaw`. **Verified 2026-07-04: this is stale** — `openclaw` has
no passwordless sudo (`sudo -n true` fails, "a password is required") and cannot even read
`/home/dgmneto/homelab` or `/footage/services` (permission denied). For anything under
`/home/dgmneto/homelab` or root-owned paths like `/footage/services/<svc>`, SSH as `dgmneto` instead —
it has `sudo` (interactive password required, ask the user) and owns the repo checkout directly.


### Remote access — Tailscale
`tailscaled` runs **natively** (apt, not Docker) as tailnet node `casaos` / `100.79.139.39`, tagged
`tag:server`, advertising subnet routes `192.168.11.0/24`, `192.168.14.0/24`, `192.168.15.0/24`, with
Tailscale SSH on. Off-LAN: `ssh dgmneto@casaos` (no 1Password agent needed) and the `*.intern` URLs work
over it. Details + why the flags matter: [services/tailscale](../../services/tailscale/README.md).

### `claude` user (agent account)
Created 2026-10-28: `claude` (uid 1306), home `/home/claude`, shell bash, groups `claude,docker`,
**passwordless sudo** via `/etc/sudoers.d/90-claude` (`claude ALL=(ALL) NOPASSWD: ALL`) — i.e. root-
equivalent; use it instead of `dgmneto` when an agent needs `sudo` non-interactively. **Login: Tailscale SSH
only** — the tailnet `ssh` rule `tag:claude → tag:server` has `users: ["claude"]` (no password, no
`authorized_keys`). Claude cloud sessions: `ssh casaos` (hook-written `~/.ssh/config` uses `User claude`);
verified 2026-10-28 `sudo -n true` OK. That rule no longer lists `dgmneto`, so `ssh dgmneto@casaos` from
a cloud session is refused ("not permit you to SSH as user dgmneto") — use `claude` + sudo. `/etc/sudoers.d/` now holds only
`90-claude` (+ README); the old `migration-task2` drop-in (dgmneto NOPASSWD for rsync/mkdir/mv/rm/sed/
usermod/find/crontab) was removed 2026-10-28 — `dgmneto` sudo always needs the password now.

### `nbbackup` user (backup sink for homelab-notebook)
Created 2026-10-30: system user `nbbackup` (uid 998), home `/footage/backups/homelab-notebook` (0700). One
`authorized_keys` entry: the laptop's backup key, forced to `rrsync -wo` (write-only into that dir), `restrict`,
`from="192.168.11.21"`. No other login. Pruned by `/etc/cron.d/homelab-notebook-backup`. Details:
[MIGRATION.md § Backups](../../services/homeassistant/MIGRATION.md#backups-live-since-2026-10-30).

## Deployment architecture

- **Orchestration:** plain `docker compose`, one directory per service under
  `/home/dgmneto/homelab/services/<svc>/compose.yaml`. List everything with `docker compose ls`.
  CasaOS is installed but **inactive** — do not manage services through it.
- **Auto-update:** `watchtower` runs `--schedule "0 0 10 * * 0" --cleanup` — **weekly, Sundays
  10:00** (verified 2026-10-25 via `docker inspect watchtower`; older notes saying "every 30 s" are
  stale). Watches **all** containers except those labelled `com.centurylinklabs.watchtower.enable=false`
  (e.g. terminus). Most images are `:latest`, so a bad upstream release still lands stack-wide weekly.
- **Self-heal:** `autoheal` restarts unhealthy containers **only if labeled `autoheal=true`** —
  currently **no container carries the label, so it is effectively a no-op**.
- **Reverse proxy:** two nginx-proxy-manager instances — `nginxProd` (public) and `nginxIntern`
  (internal/LAN).
- **DNS:** `ddns` (cloudflare-ddns) keeps the public record current.

## Networking gotcha — VPN-routed services
`qbittorrent` AND `prowlarr` have **no network of their own**: `network_mode: container:gluetunProtonVPN`
routes all their traffic through the `gluetunProtonVPN` (ProtonVPN / WireGuard, port-forwarding on)
container. If gluetun is down or restarting, both lose connectivity, and **recreating gluetun takes
them down with it**. Their WebUI ports live in gluetun's namespace (qbittorrent 9090, prowlarr 9696)
but are **not published to any host port** — they are reached only via `nginxIntern` proxying to
`gluetun:<port>`. `internalNetwork` (`172.21.0.0/24`) is an external bridge shared across stacks;
NPM and Plex also sit on a `macvlan` (VLAN 14, `192.168.14.0/24`) with static IPs.

## apt quirk
The server's 1Password apt repo (`downloads.1password.com/linux/debian`) fails `apt-get update` with
`EXPKEYSIG AC2D62742012EA22` (expired signing key, seen 2026-10-28). Harmless warning — other repos
update fine — but re-import 1Password's current key to clear it.

## Service groups
- **Media (arr stack):** prowlarr, sonarr, radarr, bazarr, qbittorrent, overseerr, plex.
- **Home automation:** **moved to homelab-notebook 2026-10-30/31** (homeassistant, zigbee2mqtt, mosquitto, matter-server);
  containers removed here, `/footage/services/{homeassistant,z2mqtt,mosquitto,matter}` kept for rollback/archive.
  casaos still holds the nightly backups of them (`/footage/backups/homelab-notebook`).
- **Displays:** terminus (TRMNL BYOS server, :2300), trmnl-ai (LLM screen generator for it,
  internalNetwork 172.21.0.141:8080, no host port).
- **Infra:** nginxProd, nginxIntern, ddns, watchtower, autoheal, gluetunProtonVPN.

## Storage layout (critical for outages)

| Mount | Size | Holds |
|-------|------|-------|
| `/` (`/dev/mmcblk0p2`) | 27G | OS root |
| `/footage` | 492G | **service configs** — e.g. `/footage/services/<svc>/config`, HA config bind-mount |
| `/library` | 3.1T | media + torrents (`/library/media`, `/library/torrent`) |

Both volumes sit on an **LVM RAID1 mirror** across two 4TB disks (rebuilt 2026-08-08 — the old pair
were failing and had no redundancy). A single disk failure is now survivable. Check with
`sudo lvs -a -o name,attr,sync_percent,devices` — healthy is `rwi-aor---` at `100.00` with each LV's
two `_rimage_` legs on **different** PVs. Read
[notes/disk-health-storage-array.md](../../notes/disk-health-storage-array.md) before touching storage; it
carries the LVM traps (allocated ≠ used, `lvreduce` frees the LV *tail*, `lvextend` desyncs new
extents) that cost real time to rediscover.

Container configs are bind-mounted from `/footage`, **media** from `/library`. A service "down" is
usually a **full disk**, not a crashed app — `df -h /footage /library` first.

## Known recurring outage: `/footage` fills to 100%
Home Assistant's config is bind-mounted on `/footage`; when `/footage` hits 100% HA crash-loops on
`OSError: [Errno 28] No space left on device` and looks "down" while `/` is fine. Past root cause was
the `openclaw` user's runaway `chrome.service` leaking `*.pma` files. If it recurs:
`find ~openclaw/.config/google-chrome*/ -name '*.pma' -delete` and confirm `chrome.service` has not
returned. Full write-up: [notes/footage-disk-leak.md](../../notes/footage-disk-leak.md).

