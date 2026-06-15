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

## Adding a proxy host without the UI

The NPM REST API works from the Mac too (HTTPS via `https://nginx.intern.dgmneto.com/api`, login
`op://Homelab/nginx`; the admin IP `192.168.14.34:81` itself is Mac-unreachable but the proxied
hostname is fine):

```
TOKEN=$(curl -sk -X POST https://nginx.intern.dgmneto.com/api/tokens \
  -H "Content-Type: application/json" \
  -d '{"identity":"<username>","secret":"<password>"}' | jq -r '.token')

curl -sk -X POST https://nginx.intern.dgmneto.com/api/nginx/proxy-hosts \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
    "domain_names": ["<svc>.intern.dgmneto.com"],
    "forward_host": "<container_name>", "forward_port": <port>,
    "access_list_id": 0, "certificate_id": 1, "ssl_forced": true,
    "http2_support": true, "allow_websocket_upgrade": true,
    "forward_scheme": "http", "enabled": true, "locations": [],
    "advanced_config": "", "meta": {"letsencrypt_agree": false, "dns_challenge": false}
  }'
```

`certificate_id: 1` is the shared `*.intern.dgmneto.com` wildcard cert used by every existing host
— reuse it. `forward_host` resolves via docker DNS on `internalNetwork`, so the target container
just needs to be on that network (no static IP needed).

## Quirks / runbook

- This is the **internal** twin of `nginxProd` (`192.168.14.33`). The two are
  identical images differing only by IP and intended scope. Add LAN-only hosts
  here; add public hosts to `nginxProd`.
- Same `/footage` storage dependency and macvlan host-unreachability caveat as
  `nginxProd`.
- Restart policy `always`.
