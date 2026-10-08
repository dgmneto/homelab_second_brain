# Logbook — hermes

Reverse-chronological. Newest entry on top. One entry per task that touches **hermes** — what
changed, why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-08 — SSH access to casaos + second-brain clone
The user wanted Hermes to be able to change casaos and keep this repo current. They chose "docker + repo,
no sudo".
- Notebook (`hermes.nix`): `hermes-ssh-keys` oneshot generates `/var/lib/hermes/.ssh/id_{casaos,github_brain}`
  (ed25519, never leave the box); `programs.ssh.extraConfig` `Match localuser hermes` blocks map
  `casaos`/`github.com` to those keys; casaos + github.com host keys pinned in `programs.ssh.knownHosts`;
  `openssh`/`git` in `extraPackages`; `GIT_{AUTHOR,COMMITTER}_*` = Hermes on `hermes-agent`.
  Switch restarted hermes-agent; all 3 bots reconnected at 10:14.
- casaos (one-time root script): user `hermes` (uid 1305) in `docker`, `passwd -l`,
  `authorized_keys` with `from="192.168.11.21",no-agent-forwarding,no-port-forwarding,no-X11-forwarding`;
  `setfacl -m u:hermes:--x /home/dgmneto`; `setfacl -R -m u:hermes:rwX,u:dgmneto:rwX` +
  default ACLs on dirs of `/home/dgmneto/homelab`; hermes git `safe.directory` + identity.
- GitHub: write deploy key "hermes@homelab-notebook" on `dgmneto/homelab_second_brain`.
- Hermes skill `skills/devops/homelab-ops/SKILL.md` (default profile only) explains how to use it.
Verified: `sudo -u hermes ssh casaos` → `id` shows docker group, write+delete a file in the repo,
`docker compose ls` works.

## 2026-10-08 — Migrated to native NixOS on homelab-notebook
Moved from Docker on casaos to the upstream `services.hermes-agent` NixOS module on `homelab-notebook`
(192.168.11.21), pinned to the same upstream rev (749220ef, v0.21.5). Config in repo
`notebook_home_lab/nixos/hermes.nix`. Cutover: 09:27:54 `docker compose stop` on casaos → tar of
`/footage/services/hermes/config` (minus 203 MB `core` dump, `.bak-*`, gateway pid/lock/sock) piped to
`/var/lib/hermes/.hermes`; 16 `*.db` md5s matched. `home/` → `/var/lib/hermes/home`, `.env` →
`/var/lib/hermes/env`, `/opt/data` paths rewritten in config/skills, stale `.local/state/hermes/gateway-locks`
removed. 10:02 all three bots `✓ telegram connected` (default, gmail-agent, orion). NPM host 23 →
`192.168.11.21:9119`, dashboard 200. Downtime ~35 min (09:28–10:03; 10 min planned — default bot waited
on a missing `.env`, see README gotcha). casaos containers stopped, not removed (rollback).
Issues hit: SQLite 3.51.2 WAL bug (fixed via 3.53.3 + LD_LIBRARY_PATH); build OOM/swap on 4 GB RAM
(nixpkgs follows); notebook stuck in emergency mode after a hardware-configuration.nix edit from
another session switched disks to `HL-*` labels before they existed (partitions relabeled).

## 2026-08-03 — Pin static IP (was colliding with nginxProd after reboot)
During recovery from a forced host reboot (see root LOGBOOK + `notes/disk-health-storage-array.md`),
found `hermes` had grabbed `172.21.0.9` on `internalNetwork` dynamically, which is `nginxProd`'s
hardcoded static IP — broke that container on boot. Added `ipv4_address: 172.21.0.250` to `hermes`'s
`intern` network block in `compose.yaml`, `docker compose up -d` to recreate. Verified:
`docker network inspect internalNetwork` shows `hermes 172.21.0.250/24`, `nginxProd` came up clean on
`.9` afterward.

## 2026-06-22 — Add read-only Docker access via socket proxy
Added `tecnativa/docker-socket-proxy` sidecar (`hermes-docker-proxy`) to compose.
Hermes now has `DOCKER_HOST=tcp://hermes-docker-proxy:2375`; proxy allows only GET
endpoints (CONTAINERS, IMAGES, NETWORKS, VOLUMES, INFO, SERVICES, TASKS). No write/exec
access. Both containers up, proxy shows "Loading success" in logs. HAProxy timeout warning
on `docker-events` backend is cosmetic/expected for this image.

## 2026-06-15 — Broaden telegram allowlist to all openclaw accounts
First pass only used `telegram-default-allowFrom.json` + 2 group IDs. User pointed out openclaw
runs multiple agent accounts (default/lobi/nutri/orion) each with their own `allowFrom` /
`groupAllowFrom` / groups in `openclaw.json`. Took the union: users `2070569244, 386325858,
6400549245` (6400549245 only appeared in orion's `groupAllowFrom`); groups `-1003925667659,
-1003616165246, -5294644290` (-5294644290 only in orion's `groups`). Updated `.env` +
`config.yaml`, `--force-recreate`, verified `✓ telegram connected` again.

## 2026-06-15 — Expose Hermes dashboard via nginxIntern
Added basic-auth creds (`HERMES_DASHBOARD_BASIC_AUTH_USERNAME/PASSWORD/SECRET`, generated, stored in
1Password Personal as "Hermes - Dashboard") to `.env`, `docker compose up -d --force-recreate`.
Confirmed `docker exec hermes env` does NOT show these (or the API keys) — Hermes loads
`/opt/data/.env` itself at startup, compose `environment:`/`env_file` not needed for app secrets.

Created NPM proxy host via API (`https://nginx.intern.dgmneto.com/api`, creds `op://Homelab/nginx`):
id 23, `hermes.intern.dgmneto.com` -> `hermes:9119`, cert_id 1 (shared `*.intern.dgmneto.com` cert),
`allow_websocket_upgrade: true`. Verified `https://hermes.intern.dgmneto.com/login` returns 200.

## 2026-06-15 — New service: Hermes AI agent (Telegram + OpenRouter)
Deployed NousResearch Hermes Agent as a new docker compose service, per
https://hermes-agent.nousresearch.com/docs/user-guide/docker.

Created `/home/dgmneto/homelab/services/hermes/compose.yaml` (internalNetwork only, no published
ports, `mem_limit 2g`/`cpus 1`, `no-new-privileges`, `pids_limit 256`, tmpfs `/tmp`) and
`/footage/services/hermes/config` (root:root — top-level `/footage/services/*` dirs require root to
create; container runs as root and can write fine, so no chown needed).

Wrote `config.yaml` (provider: openrouter, model `anthropic/claude-sonnet-4`) and `.env`
(`OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`) into the config dir via a
throwaway `alpine` container (host user can't write directly to root-owned dir). Both new secrets
also stored in 1Password Personal ("Hermes - OpenRouter API key", "Hermes - Telegram Bot Token").

Telegram allowlist copied from the existing `openclaw` agent's
`/footage/home/openclaw/.openclaw/credentials/telegram-default-allowFrom.json`
(users `2070569244`, `386325858`) plus two group IDs found in `.openclaw/openclaw.json`
(`-1003616165246`, `-1003925667659`).

Isolation decision: no dedicated Linux user — container hardening only, consistent with every other
service. (Server already has a separate `openclaw` user, but that's for a different, pre-existing
agent with host-level access; not reused here.)

`docker compose up -d`, then `--force-recreate` after adding the allowlist. Verified via
`/opt/data/logs/agent.log`: `✓ telegram connected`, no allowlist-deny warning. `docker stats`:
~180MB/2GB RAM at idle.
