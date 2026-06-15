# hermes

AI agent (NousResearch Hermes Agent) — chat assistant reachable via Telegram, using OpenRouter as
model provider.

## Image
`nousresearch/hermes-agent:latest` (tag not pinned, ~3.3GB)

## Access
- Telegram bot (token in `/footage/services/hermes/config/.env`, see "Secrets" below).
- Dashboard: https://hermes.intern.dgmneto.com (NPM proxy host id 23 -> `hermes:9119`, cert_id 1,
  websocket upgrade on). Login form (not HTTP basic auth) — creds = `HERMES_DASHBOARD_BASIC_AUTH_*`
  from `.env`, also stored in 1Password Personal as "Hermes - Dashboard".
- No host ports published — `internalNetwork` only; dashboard reachable only via the NPM proxy.

## Compose
`/home/dgmneto/homelab/services/hermes/compose.yaml`

## Config path
`/footage/services/hermes/config` -> `/opt/data` (single mount: `.env`, `config.yaml`, sessions/,
memories/, skills/, logs/). Created `root:root` — container runs as root by default, can still
write; don't `chown` unless you also adjust the container user.

## Secrets (`/footage/services/hermes/config/.env`, chmod 600, NOT in repo)
- `OPENROUTER_API_KEY` — dedicated key, also stored in 1Password Personal as "Hermes - OpenRouter
  API key".
- `TELEGRAM_BOT_TOKEN` — also stored in 1Password Personal as "Hermes - Telegram Bot Token".
- `TELEGRAM_ALLOWED_USERS` — comma-separated user/group IDs. Currently copied from openclaw's
  `telegram-default-allowFrom.json` (`2070569244,386325858`) plus two group IDs
  (`-1003616165246,-1003925667659`) found in `/footage/home/openclaw/.openclaw/openclaw.json`.
- `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` / `_PASSWORD` / `_SECRET` — dashboard login. App reads
  these from `/opt/data/.env` itself (not exposed via `docker exec env`) — same mechanism as the
  API keys above, no compose `environment:` entry needed.

## Config (`config.yaml`, non-secret)
```yaml
model:
  provider: "openrouter"
  default: "anthropic/claude-sonnet-4"

telegram:
  allowed_users: [2070569244, 386325858, -1003616165246, -1003925667659]
```

## Networks
`internalNetwork` (`intern`) only, no static IP, no published ports.

## Isolation / hardening
No dedicated Linux user — container-level hardening only (matches every other service here):
`security_opt: no-new-privileges`, `pids_limit: 256`, `mem_limit: 2g`, `cpus: 1.0`, tmpfs `/tmp`
(noexec,nosuid). Host has only ~4G RAM headroom — keep an eye on `docker stats hermes` if enabling
heavier tools (browser/Playwright etc.).

## Quirks / runbook
- First boot installs ~70 bundled skills + Playwright Chromium — takes ~1-2 min, normal.
- s6 gateway logs at `/opt/data/logs/gateways/default/current` (inside container) — `tail` it to
  confirm `✓ telegram connected`. Without `TELEGRAM_ALLOWED_USERS` set, gateway logs a WARNING and
  silently denies all chats (not a crash).
- To write into `/opt/data` from the host (it's `root:root`, dgmneto can't write directly), use a
  throwaway container: `docker run --rm -v /footage/services/hermes/config:/opt/data alpine sh -c "..."`.
- `docker compose up -d --force-recreate` to apply `.env`/`config.yaml` changes (gateway doesn't
  hot-reload `.env`).
