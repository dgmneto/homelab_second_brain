# Logbook — hermes

Reverse-chronological. Newest entry on top. One entry per task that touches **hermes** — what
changed, why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

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
