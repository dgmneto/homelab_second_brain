# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is a **second brain** for the homelab server — a knowledge base of notes, runbooks, and
service docs. It is **not** the deployment. There is no application code to build, lint, or test here.

The actual deployment (docker-compose stacks) lives **on the server itself** at
`/home/dgmneto/homelab` and is version-controlled separately at `git@github.com:dgmneto/homelab.git`.
When asked to change a service, you edit compose files on the server, not in this repo.

Service-specific knowledge goes in subfolders under `./services/<service-name>/`.

## Accessing the server

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

For the deployment user add `-o User=openclaw`. The user holds the `sudo` password; pipe via `sudo -S`
for non-interactive use.

## Accessing service web UIs (Claude-in-Chrome)

Every service with a web UI is reachable through the **Claude in Chrome** browser extension by driving
the user's local Chrome — the same Chrome that sits on/behind the home network, so it resolves the
nginx-proxy-manager hostnames that are not exposed to the public internet.

- **Internal hostnames (via `nginxIntern`):** `https://<service>.intern.dgmneto.com`
  (verified: `overseerr.intern.dgmneto.com`, also `qbittorrent.intern.dgmneto.com`,
  `prowlarr.intern.dgmneto.com`). qBittorrent/prowlarr proxy into the gluetun namespace.
- **Public hostnames (via `nginxProd`):** e.g. Plex at `https://filmin.3e.dgmneto.com`.

Full authoritative URL list + which credential governs each UI is in `ACCESS.md` (pulled from the NPM
databases). Note: the 1Password vault holds **no app-UI logins** — only infra secrets — so most UIs
have no `op://` password to retrieve; see `ACCESS.md`.

How: `list_connected_browsers` → `switch_browser` (user clicks Connect in the right Chrome) →
`tabs_context_mcp` (create a tab) → `navigate` to the hostname → `read_page`/screenshot/`computer` to
drive it. Reaching `*.intern.dgmneto.com` requires the user's Chrome to be on the LAN (or via their
remote-access path); an off-network browser won't resolve them. Do not type secrets into login forms —
pull from 1Password and have the user authenticate.

## Secrets — 1Password (`op` CLI)

Homelab secrets live in 1Password. The `op` CLI (v2.30+) is installed on the Mac and authenticated via
**desktop-app integration** — no manual `op signin` needed as long as the 1Password app is unlocked
(same app whose SSH agent signs GitHub pushes). Account: `dgmneto@gmail.com` / `my.1password.com`.

Vaults: **`Homelab`** (server/service secrets) and `Personal`. Find and read:
```
op vault list
op item list --vault Homelab                      # titles + categories
op item list --vault Homelab --format json | jq    # scriptable
op item get "<title>" --vault Homelab              # full item
op read "op://Homelab/<title>/password"            # one field, by secret reference
```
Known `Homelab` items: `Plex - Claim`, `Cloudflare - DDNS`, `ProtonVPN - Gluetun`,
`Service Account Auth Token: Homelab`. (No qBittorrent item yet — relevant to the leaked watchdog
password noted in `services/plex-qbittorrent-watchdog/README.md`.)

Rules:
- **Never** paste a retrieved secret value into a file, commit, logbook, or this repo. Reference
  secrets by their `op://` path instead.
- To wire a secret into a service, prefer reading it at run time (`op read`) or templating with
  `op inject`/`op run` on the server — do not bake literals into compose `.env` or scripts.

## Deployment architecture (on the server)

- **Orchestration:** plain `docker compose`, one directory per service under
  `/home/dgmneto/homelab/services/<svc>/compose.yaml`. List everything with `docker compose ls`.
  CasaOS is installed but **inactive** — do not manage services through it.
- **Auto-update:** `watchtower` runs `--interval 30 --cleanup` — polls **every 30 seconds**, watches
  **all** containers (no label filter), prunes old images. Nothing is version-pinned (`:latest`
  everywhere), so a bad upstream release can propagate across the whole stack almost immediately.
- **Self-heal:** `autoheal` restarts unhealthy containers **only if labeled `autoheal=true`** —
  currently **no container carries the label, so it is effectively a no-op**.
- **Reverse proxy:** two nginx-proxy-manager instances — `nginxProd` (public) and `nginxIntern`
  (internal/LAN).
- **DNS:** `ddns` (cloudflare-ddns) keeps the public record current.

### Networking gotcha — VPN-routed services
`qbittorrent` AND `prowlarr` have **no network of their own**: `network_mode: container:gluetunProtonVPN`
routes all their traffic through the `gluetunProtonVPN` (ProtonVPN / WireGuard, port-forwarding on)
container. If gluetun is down or restarting, both lose connectivity, and **recreating gluetun takes
them down with it**. Their WebUI ports live in gluetun's namespace (qbittorrent 9090, prowlarr 9696)
but are **not published to any host port** — they are reached only via `nginxIntern` proxying to
`gluetun:<port>`. `internalNetwork` (`172.21.0.0/24`) is an external bridge shared across stacks;
NPM and Plex also sit on a `macvlan` (VLAN 14, `192.168.14.0/24`) with static IPs.

### Service groups
- **Media (arr stack):** prowlarr, sonarr, radarr, bazarr, qbittorrent, overseerr, plex.
- **Home automation:** homeassistant, zigbee2mqtt (`z2mqtt`), mosquitto (MQTT broker), matter-server.
- **Infra:** nginxProd, nginxIntern, ddns, watchtower, autoheal, gluetunProtonVPN.

## Storage layout (critical for outages)

| Mount | Size | Holds |
|-------|------|-------|
| `/` (`/dev/mmcblk0p2`) | 27G | OS root |
| `/footage` | 492G | **service configs** — e.g. `/footage/services/<svc>/config`, HA config bind-mount |
| `/library` | 3.1T | media + torrents (`/library/media`, `/library/torrent`) |

Container configs are bind-mounted from `/footage`, **media** from `/library`. A service "down" is
usually a **full disk**, not a crashed app — `df -h /footage /library` first.

### Known recurring outage: `/footage` fills to 100%
Home Assistant's config is bind-mounted on `/footage`; when `/footage` hits 100% HA crash-loops on
`OSError: [Errno 28] No space left on device` and looks "down" while `/` is fine. Past root cause was
the `openclaw` user's runaway `chrome.service` leaking `*.pma` files. If it recurs:
`find ~openclaw/.config/google-chrome*/ -name '*.pma' -delete` and confirm `chrome.service` has not
returned. See `services/` notes and the `homelab-footage-chrome-leak` memory.

## Working conventions

- Document a service: create/update `./services/<service-name>/` with what you learned (ports, config
  paths, quirks, runbooks). Keep it server-truth, not guesses.
- When changing a running service, edit the compose file **on the server** under
  `/home/dgmneto/homelab/services/<svc>/`, then `docker compose up -d` in that directory.

## MANDATORY — keep notes and logbooks current (every task)

This is the whole point of the repo. On **every** task, before you finish:

1. **Update the affected `services/<svc>/README.md`** if anything you learned or changed makes it
   stale — new port, path, quirk, integration, runbook step. Server-truth only.
2. **Append a logbook entry.** Two scopes of logbook exist:
   - `./LOGBOOK.md` — root, project-wide. Log every task here.
   - `./services/<svc>/LOGBOOK.md` — one per service. Also log here when a task touched that service.
   A task that touched 2 services → 1 root entry + 2 service entries.

Logbook rules:
- **Reverse chronological** — newest entry on top, directly under the header.
- One entry per task. Format:
  ```
  ## YYYY-MM-DD — <short title>
  What changed and why. Commands run on the server. Outcome (verified how).
  ```
- Use the real date. Record what was actually done/verified, not intentions. If a task only read
  state (no change), still log it as an investigation entry.

3. **Commit and push ASAP.** Every notes/logbook update must be `git commit`ted and `git push`ed to
   `origin main` (`git@github.com:dgmneto/homelab_second_brain.git`) as soon as the task is done —
   do not leave the working tree dirty between tasks. The repo is the durable record; an unpushed
   change is a lost change. (GitHub auth uses the 1Password SSH agent — if it is locked, signing
   fails; unlock it and retry. The on-disk `id_rsa` is the *homelab server* key, not GitHub's.)
