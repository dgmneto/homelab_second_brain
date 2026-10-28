# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read this first — this repo is built for agents to improve

This is a **second brain** for the homelab, optimized for the agents that read it. **You are not just a
consumer of these notes — you are their maintainer.** Every agent that runs here must actively leave the
repo better for the next iteration than it found it.

Operating rules for every task:
- **Fix the repo the moment reality contradicts it.** If you acted on a note/README/ACCESS/runbook and
  it was wrong, stale, or misleading, **correct it in the same task** — don't just work around it. The
  bug is the documentation, not just the situation.
- **Capture every mistaken assumption you had to recover from.** If you wasted a step on a wrong guess
  (wrong path, wrong hostname, wrong auth, a tool that overflowed, a command that doesn't exist here),
  write the correction down where the *next* agent will hit it first, so they never make that guess.
  The qBittorrent runbook (`read_page` overflows → use a screenshot; all-stopped-at-0B = watchtower
  restart, not the watchdog) is the model: record the gotcha AND the shortcut.
- **Move/rename/restructure freely** when the current layout caused the confusion. Put facts where an
  agent would look for them, add cross-links, split or merge files. Don't preserve a bad structure out
  of caution — improving navigability is part of the job.
- **Prefer durable fixes over notes.** If something keeps biting (e.g. a literal that should be an
  `op://` reference, a missing permission, an unpinned image), fix the root cause and document that you
  did, rather than leaving a "watch out for this" forever.
- **Leave breadcrumbs as you go**, not just at the end: a new quirk, a verified command, a corrected
  IP/port — append it to the right README/ACCESS/LOGBOOK immediately, then commit + push (see below).

Treat anything in here as provisional: if a recalled fact, file, flag, or hostname doesn't match what
the server actually shows, trust the server and update the repo.

## What this repo is

It is **not** the deployment. There is no application code to build, lint, or test here.
Durable cross-cutting facts (the "project memory") live in [notes/](notes/); per-machine knowledge in
`hosts/<host>/`; per-service knowledge in `services/<svc>/`. This repo is the single source of truth — keep memory here, not in scratch stores.

The casaos deployment (docker-compose stacks) lives **on that server** at `/home/dgmneto/homelab`,
version-controlled separately at `git@github.com:dgmneto/homelab.git` — to change a casaos service you
edit compose files on the server, not in this repo. Exception: homelab-notebook's NixOS config *is* in
this repo (`hosts/homelab-notebook/nixos/`) and is deployed from here.

Knowledge has two axes:
- **`hosts/<hostname>/`** — one per machine: hardware, OS, SSH access, storage, deploy method,
  host-level cron/timers, host LOGBOOK. Index: [hosts/README.md](hosts/README.md).
- **`services/<service>/`** — one per service, flat regardless of host; each README says where it runs.
  Service → host map: [services/README.md](services/README.md).
- **`notes/`** — cross-cutting memories (this folder *is* the harness auto-memory symlink; don't move it).

Rule of thumb: "is it about the box or about the app?" Disk/OS/SSH/cron → `hosts/`; ports/config/
quirks of one app → `services/`.

## Hosts — read the host README before touching a box

| Host | IP | Runtime | SSH | Read |
|---|---|---|---|---|
| `casaos` (alias `homelab`) | `192.168.11.13` | x86_64 Debian 12, docker compose | `ssh dgmneto@homelab` | [hosts/casaos/README.md](hosts/casaos/README.md) |
| `homelab-notebook` | `192.168.11.21` | NixOS 26.05, native modules | `ssh homelab-notebook` | [hosts/homelab-notebook/README.md](hosts/homelab-notebook/README.md) |

Top gotchas (detail in the host READMEs):
- **casaos** is x86_64, not a Raspberry Pi. If the 1Password SSH agent is locked, bypass it:
  `ssh -o IdentityAgent=none -o IdentitiesOnly=yes -i ~/.ssh/id_rsa dgmneto@homelab`. Use `dgmneto`
  (sudo needs the user's password), not `openclaw`. A service "down" is usually a **full disk** —
  `df -h /footage /library` first. Both volumes are on an LVM RAID1 mirror; read
  [notes/disk-health-storage-array.md](notes/disk-health-storage-array.md) before touching storage.
- **casaos** runs Tailscale natively (node `casaos`, subnet router for .11/.14/.15, Tailscale SSH) —
  remote access path when off-LAN; see [services/tailscale](services/tailscale/README.md). Claude **cloud** sessions join automatically via the SessionStart hook `.claude/hooks/session-start.sh` (uses the injected `TS_AUTHKEY`) and can then `ssh casaos` as user `claude` (Tailscale SSH, no key, passwordless sudo; details in that README).
- **casaos** `qbittorrent` + `prowlarr` live in `gluetunProtonVPN`'s network namespace — recreating
  gluetun takes them down. watchtower updates everything weekly (Sun 10:00); autoheal is a no-op.
- **homelab-notebook**: key exists only in 1Password — if it's locked you are locked out (no fallback),
  and the Bash sandbox can't reach the agent socket (disable sandbox for ssh/op). Its NixOS flake is
  **in this repo** at `hosts/homelab-notebook/nixos/`; `git diff` before every deploy. Hermes on it
  pushes to this repo, so `git pull --rebase` before editing.

## Accessing service web UIs (Claude-in-Chrome)

Every service with a web UI is reachable through the **Claude in Chrome** browser extension by driving
the user's local Chrome — the same Chrome that sits on/behind the home network, so it resolves the
nginx-proxy-manager hostnames that are not exposed to the public internet.

- **Internal hostnames (via `nginxIntern`):** `https://<service>.intern.dgmneto.com`
  (verified: `overseerr.intern.dgmneto.com`, also `qbittorrent.intern.dgmneto.com`,
  `prowlarr.intern.dgmneto.com`). qBittorrent/prowlarr proxy into the gluetun namespace.
- **Public hostnames (via `nginxProd`):** e.g. Plex at `https://filmin.3e.dgmneto.com`.

Full authoritative URL list + which credential governs each UI is in `ACCESS.md` (pulled from the NPM
databases). The `Homelab` vault *does* hold some app-UI logins (qbittorrent, Prowlarr, Sonarr, Radarr,
Plex, nginx, NGINX Prod) — check `op item list --vault Homelab` before assuming none; see `ACCESS.md`.

How: `list_connected_browsers` → `switch_browser` (user clicks Connect in the right Chrome) →
`tabs_context_mcp` (create a tab) → `navigate` to the hostname → `read_page`/screenshot/`computer` to
drive it. Reaching `*.intern.dgmneto.com` requires the user's Chrome to be on the LAN (or via their
Tailscale — see [services/tailscale](services/tailscale/README.md)). The names resolve publicly (to
private `192.168.14.34`), so off-network they resolve but are unreachable without Tailscale. Do not type secrets into login forms —
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
Known `Homelab` items (2026-10-28): `Plex - Claim`, `Cloudflare - DDNS`, `ProtonVPN - Gluetun`,
`Service Account Auth Token: Homelab`, `Terminus`, and LOGINs `qbittorrent`, `Prowlarr`, `Sonarr`,
`Radarr`, `Plex`, `nginx`, `NGINX Prod`. **Not everything is in Homelab**: Tailscale lives in
`Personal/Tailscale` (auth keys as fields, e.g. `op://Personal/Tailscale/CasaOs Auth Key`), Terminus
login in `Personal/Terminus`. (The `qbittorrent` item now exists, so the leaked literal password in
`services/plex-qbittorrent-watchdog/README.md` can be moved to an `op://` reference.) Search all vaults when a title isn't found:
`op item list --format json | jq -r '.[] | select(.title|test("<name>";"i")) | "\(.vault.name)\t\(.title)"'`.

Rules:
- **Never** paste a retrieved secret value into a file, commit, logbook, or this repo. Reference
  secrets by their `op://` path instead.
- To wire a secret into a service, prefer reading it at run time (`op read`) or templating with
  `op inject`/`op run` on the server — do not bake literals into compose `.env` or scripts.


## Working conventions

- Document a service: create/update `./services/<service-name>/` with what you learned (ports, config
  paths, quirks, runbooks) and add/keep its row in `services/README.md` (service → host). Keep it
  server-truth, not guesses.
- Document a machine (disks, OS, users, SSH, cron/timers, hardware): `./hosts/<hostname>/`.
- Changing a casaos service: edit the compose file **on the server** under
  `/home/dgmneto/homelab/services/<svc>/`, then `docker compose up -d` in that directory.
- Changing a homelab-notebook service: edit `hosts/homelab-notebook/nixos/`, deploy per its README.

## MANDATORY — keep notes and logbooks current (every task)

This is the whole point of the repo. On **every** task, before you finish:

1. **Update the affected `services/<svc>/README.md` / `hosts/<host>/README.md`** if anything you learned or changed makes it
   stale — new port, path, quirk, integration, runbook step. Server-truth only.
2. **Append a logbook entry.** Two scopes of logbook exist:
   - `./LOGBOOK.md` — root, project-wide. Log every task here.
   - `./services/<svc>/LOGBOOK.md` — one per service. Also log here when a task touched that service.
   - `./hosts/<host>/LOGBOOK.md` — one per machine. Log here for host-level changes (disks, OS, users,
     cron/timers, NixOS deploys, hardware).
   A task that touched 2 services on one host's disk → 1 root entry + 2 service entries + 1 host entry.

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
