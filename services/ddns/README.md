# ddns — Cloudflare Dynamic DNS

Keeps a public Cloudflare DNS record pointed at the homelab's current WAN IP.
Polls the host's external IP and updates the Cloudflare A record when it changes,
so inbound traffic (via `nginxProd`) keeps resolving after an ISP IP change.

## Image

`oznu/cloudflare-ddns:latest` (container: `ddns`)

> Pinned to `:latest`. Auto-updated by Watchtower (see `../watchtower`).

## Access

No exposed ports — outbound-only background worker. Runs an internal cron loop
that re-checks periodically.

## Compose

Server path: `/home/dgmneto/homelab/services/ddns/compose.yaml`

Uses `env_file: ".env"` — all configuration comes from environment variables.

## Configuration (env key NAMES only — values are secret)

`.env` keys at `/home/dgmneto/homelab/services/ddns/.env`:

- `API_KEY` — Cloudflare API token. **Secret — never commit or print its value.**
- `ZONE` — Cloudflare zone (the apex domain, e.g. `dgmneto.com`).
- `SUBDOMAIN` — record updated within the zone (observed managing `3e.dgmneto.com`).

## Networks

None declared — runs on its own default bridge (`ddns_default`). Only needs
outbound internet to reach the Cloudflare API and an IP-echo endpoint.

## Integrations / scope

- Pairs with `nginxProd`: ddns keeps the public hostname resolving to the WAN IP;
  `nginxProd` terminates and routes the inbound traffic.
- Single record (`SUBDOMAIN` in `ZONE`).

## Quirks / runbook

- Healthy logs read `No DNS update required for 3e.dgmneto.com (<ip>).` on every
  cycle — that is the steady state, not an error.
- If the public hostname stops resolving: `docker logs ddns`. Common causes are
  an expired/insufficient-scope Cloudflare token (`API_KEY`) or a `ZONE`/`SUBDOMAIN`
  mismatch.
- **Never write the Cloudflare token into this repo.** It lives only in the
  server-side `.env`.
- Restart policy `always`.
