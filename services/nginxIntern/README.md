# nginxIntern — Internal/LAN Nginx Proxy Manager

Second Nginx Proxy Manager instance dedicated to **internal / LAN-only** proxy
hosts. Keeps internal services (and their hostnames/certs) separated from the
public edge proxy so they are never exposed to the internet.

## Image

`jc21/nginx-proxy-manager:latest` (container: `nginxIntern`)

> Pinned to `:latest`. Auto-updated by Watchtower (see `../watchtower`).

## Access

- **80/tcp** — HTTP
- **443/tcp** — HTTPS (proxied traffic)
- **81/tcp** — NPM admin web UI

Reachable on its macvlan IP `192.168.14.34` (admin at `http://192.168.14.34:81`).
Admin credentials live in NPM's own database, not in compose.

## Compose

Server path: `/home/dgmneto/homelab/services/nginxIntern/compose.yaml`

No `.env` file.

## Config / persistent data

Bind-mounted from `/footage/`:

- `/footage/services/nginxIntern/data` → `/data` — NPM database, proxy hosts,
  access lists.
- `/footage/services/nginxIntern/letsEncrypt` → `/etc/letsencrypt` — certs.

Proxy-host config is held in `/data` (SQLite), managed through the admin UI.

## Networks

Same two external networks as `nginxProd`, different static IPs:

- `macVlanNetwork` (macvlan, parent `enp3s0.14`, `192.168.14.0/24`) —
  static IP **192.168.14.34**.
- `internalNetwork` (bridge, `172.21.0.0/24`) — static IP **172.21.0.83**.

Both declared `external: true`.

## Quirks / runbook

- This is the **internal** twin of `nginxProd` (`192.168.14.33`). The two are
  identical images differing only by IP and intended scope. Add LAN-only hosts
  here; add public hosts to `nginxProd`.
- Same `/footage` storage dependency and macvlan host-unreachability caveat as
  `nginxProd`.
- Restart policy `always`.
