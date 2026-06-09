# nginxProd — Public Nginx Proxy Manager

Public-facing reverse proxy / TLS terminator for the homelab. This is the
internet-exposed NPM instance: it fronts services that should be reachable from
outside the LAN and manages their Let's Encrypt certificates.

## Image

`jc21/nginx-proxy-manager:latest` (container: `nginxProxyManagerProd`)

> Pinned to `:latest`. Auto-updated by Watchtower (see `../watchtower`).

## Access

- **80/tcp** — HTTP (ACME challenges, redirects)
- **443/tcp** — HTTPS (proxied traffic)
- **81/tcp** — NPM admin web UI

Reachable on its macvlan IP `192.168.14.33` (e.g. admin at `http://192.168.14.33:81`).
Admin credentials are stored inside NPM's own database, not in compose.

## Compose

Server path: `/home/dgmneto/homelab/services/nginxProd/compose.yaml`

No `.env` file.

## Config / persistent data

Bind-mounted from `/footage/`:

- `/footage/services/nginxProd/data` → `/data` — NPM database, proxy host
  definitions, access lists, custom nginx snippets.
- `/footage/services/nginxProd/letsEncrypt` → `/etc/letsencrypt` — issued certs.

All proxy-host configuration lives in `/data` (SQLite), edited via the admin UI.

## Networks

Joins two external networks:

- `macVlanNetwork` (macvlan, parent `enp3s0.14`, subnet `192.168.14.0/24`,
  gw `192.168.14.1`) — static IP **192.168.14.33**. Gives the proxy its own
  L2 address on the VLAN so ports 80/443 don't collide with the host.
- `internalNetwork` (bridge, `172.21.0.0/24`) — static IP **172.21.0.9**.
  Used to reach backend containers (sonarr, radarr, overseerr, etc.) by their
  internal addresses.

Both networks are declared `external: true` and must exist before `up`.

## Quirks / runbook

- **Two NPM instances exist.** This one (`nginxProd`) is the public edge;
  `nginxIntern` (`192.168.14.34`) serves LAN-only hosts. Don't add internal-only
  proxy hosts here — they'd be exposed to the configured public path.
- Data lives under `/footage`. Watch for the recurring `/footage` Chrome
  crash-loop outage (see auto-memory); if `/footage` fills, NPM can't write its
  DB and proxying degrades.
- macvlan means the container is NOT reachable from the Docker host itself by
  its macvlan IP (standard macvlan limitation); use the `internalNetwork` IP
  from the host if needed.
- Restart policy `always`.
