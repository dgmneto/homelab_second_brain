# hermes

AI agent (NousResearch Hermes Agent) — three Telegram bots, OpenRouter as model provider.

> **Moved 2026-10-08:** runs **natively on NixOS on `homelab-notebook` (192.168.11.21)**, not Docker on
> casaos. The casaos containers (`hermes`, `hermes-docker-proxy`) are **stopped, not removed** — kept
> for rollback until ~2026-10-15. See LOGBOOK 2026-10-08 and "Rollback" below.

## Where it lives
- Host: `homelab-notebook` (Acer Aspire A315-34, NixOS 26.05). Access: `ssh homelab-notebook`
  (key only in 1Password, item "homelab-notebook SSH" — 1Password must be unlocked).
- Config (Nix, in git): `~/notebook_home_lab/nixos/hermes.nix` on the Mac (repo `notebook_home_lab`),
  deployed by rsync to `~/nixos` on the notebook + `sudo nixos-rebuild switch --flake path:.#homelab-notebook`.
- Module: upstream `hermes-agent.nixosModules.default`, flake input pinned to
  `749220ef0007f8d87bd1531f1c24b0fe93816385` (v0.21.5, 2026.9.24 — same as the last Docker image).
  `hermes-agent.inputs.nixpkgs.follows = "nixpkgs"` because evaluating Hermes' own nixpkgs swaps the
  4 GB box to death. Revisit after RAM upgrade.
- Units: `hermes-agent` (gateway, serves all 3 profiles in one process — "multiplex", upstream
  default) and `hermes-backend` (dashboard on `0.0.0.0:9119`). User `hermes`.
- Data: `/var/lib/hermes/.hermes` (= HERMES_HOME, was `/opt/data`), agent HOME `/var/lib/hermes/home`
  (was `/opt/data/home`). Logs: `/var/lib/hermes/.hermes/logs/agent.log`, per profile
  `profiles/<p>/logs/agent.log`; also `journalctl -u hermes-agent`.

## Profiles / bots (all in one gateway)
| Profile | Bot | Notes |
|---|---|---|
| default | main bot | allowlist in `TELEGRAM_ALLOWED_USERS` / `config.yaml` |
| gmail-agent | "Pijy" (for Divino) | email via `himalaya` (`HIMALAYA_CONFIG` → `profiles/gmail-agent/config/himalaya.toml`) |
| orion | orion | Sonarr/Radarr via `https://{sonarr,radarr}.intern.dgmneto.com` |

Each profile has its own `profiles/<p>/.env` (own `TELEGRAM_BOT_TOKEN`, OpenRouter key). Verify health:
`sudo grep "telegram connected" /var/lib/hermes/.hermes/logs/agent.log | tail -3` → one line per profile.

## Secrets
- Default profile secrets live in `/var/lib/hermes/env` (0600, NOT in git): `OPENROUTER_API_KEY`,
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_HOME_CHANNEL[_THREAD_ID]`,
  `HERMES_DASHBOARD_BASIC_AUTH_{USERNAME,PASSWORD,SECRET}`, `API_SERVER_KEY`. 1Password Personal:
  "Hermes - OpenRouter API key", "Hermes - Telegram Bot Token", "Hermes - Dashboard". TODO: sops-nix.
- **Gotcha:** the module writes `$HERMES_HOME/.env` from `/var/lib/hermes/env` **only at activation**
  (`nixos-rebuild switch` / `switch-to-configuration`), not at service start. If `.env` is missing
  (e.g. after restoring data), the default bot silently doesn't connect and the dashboard has no
  login. Fix: `sudo /run/current-system/bin/switch-to-configuration switch && sudo systemctl restart hermes-agent hermes-backend`.

## Dashboard
https://hermes.intern.dgmneto.com — NPM (nginxIntern on casaos) proxy host **23** → `http://192.168.11.21:9119`
(websocket on). Login form, creds = `HERMES_DASHBOARD_BASIC_AUTH_*` ("Hermes - Dashboard" in 1Password).
- Hermes rejects unknown Host headers; `settings.dashboard.public_url` declares the public name.
- Notebook firewall allows 9119 only from `192.168.14.34` (nginxIntern macvlan) and `192.168.11.13`.

## Config
Nix pins only `model` (`openrouter` / `qwen/qwen3.8-max`) and `dashboard.public_url`; the rest of
`config.yaml` is agent-managed on disk and survives rebuilds (module deep-merges). `hermes config set`
is blocked in managed mode — change `hermes.nix` instead.

## Quirks
- **SQLite:** nixos-26.05 has SQLite 3.51.2 (WAL-reset corruption bug). `hermes.nix` builds 3.53.3 and
  injects it via `LD_LIBRARY_PATH` on both units. Check: `sudo grep libsqlite3 /proc/$(systemctl show hermes-agent -p MainPID --value)/maps`.
- **False warning** "Stale systemd unit detected ... TimeoutStopSec=90s": Hermes queries
  `systemctl --user` first and gets the default. Real value is 4 min (`systemctl show hermes-agent -p TimeoutStopUSec`). Ignore.
- No Docker anywhere on the notebook → the old read-only docker-socket-proxy access is gone (accepted).
- Native mode: agent can't `pip`/`apt` install. Extra tools go in `extraPackages` (himalaya, chromium,
  curl, jq, python3); Python extras via `extraDependencyGroups`.
- Building Hermes on this box is slow (npm/uv2nix, ~1h first time, heavy swap). If the nix-daemon
  balloons, kill the build and `sudo systemctl restart nix-daemon` — finished steps are kept.

## casaos access + second brain (added 2026-10-08)
- `ssh casaos` (as unix user `hermes` on the notebook) → casaos user **`hermes`**: `docker` group,
  rwX ACL on `/home/dgmneto/homelab`, **no sudo** (password locked). `docker` group is root-equivalent
  if abused. Every profile (including gmail-agent, which reads untrusted email) runs as the same unix
  user, so they all share this access.
- Key-only, `from="192.168.11.21"` in casaos `~hermes/.ssh/authorized_keys`, so **if the notebook's
  DHCP address changes, access breaks**. Reserve .21 on the router.
- Keys: `/var/lib/hermes/.ssh/id_casaos`, `id_github_brain` (generated by the `hermes-ssh-keys` unit).
  ssh reads the passwd home `/var/lib/hermes`, not `$HOME` (`/var/lib/hermes/home`). Client config +
  pinned host keys live in `/etc/ssh/ssh_config` / `ssh_known_hosts` (from `hermes.nix`).
- Second brain: clone at `/var/lib/hermes/home/homelab`, pushes as "Hermes" via write deploy key
  "hermes@homelab-notebook" on `dgmneto/homelab_second_brain`. **Pull before editing on the Mac too**, since
  Hermes pushes here now.
- Hermes can commit in `/home/dgmneto/homelab` on casaos but **cannot push** it (no GitHub key there).
- Instructions to Hermes: skill `~/.hermes/skills/devops/homelab-ops/SKILL.md` (default profile only).
- Revoke: casaos `sudo usermod -L -e 1 hermes` (or delete `~hermes/.ssh/authorized_keys`); GitHub
  repo settings → Deploy keys → delete.
- Files Hermes creates in the deployment repo are owned by `hermes`; `dgmneto` keeps access through
  default ACLs. If `git` complains about permissions, re-run the `setfacl -R` lines from LOGBOOK.

## Rollback (until the casaos containers are removed)
1. `ssh homelab-notebook 'sudo systemctl stop hermes-agent hermes-backend'`
2. On casaos: `cd ~/homelab/services/hermes && docker compose start`
3. NPM proxy host 23 forward back to `hermes:9119`.
Note casaos data is the 2026-10-08 09:27 snapshot — anything after that lives only on the notebook.

## History
Ran on casaos in Docker 2026-06-15 → 2026-10-08 (`nousresearch/hermes-agent:latest`,
`/footage/services/hermes/config` owned by uid 10000 — not root as earlier notes said — with s6
supervising the gateway inside the container).
