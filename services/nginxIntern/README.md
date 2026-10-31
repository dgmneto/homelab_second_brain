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

### Advanced config gotcha: `rewrite` doesn't change the proxied path
NPM's `conf.d/include/proxy.conf` does `proxy_pass $forward_scheme://$server:$port$request_uri;` —
`$request_uri` is the *original* URI, so a server-level `rewrite` in a host's Advanced tab is
silently ignored upstream. To remap a path, add an exact `location = /old { proxy_set_header Host
$host; ... proxy_pass $forward_scheme://$server:$port/new$is_args$args; }` instead (example: proxy
host 25 / terminus, `/api/setup/` → `/api/setup`). **Beware:** a location ending in `/` that uses
`proxy_pass` makes nginx return **301** for the same URI without the slash — that broke newer TRMNL
firmware, so that terminus shim was removed again (host 25 Advanced is now empty). Advanced config lives in NPM's DB, not git — it
is recorded in the service README that needs it.

## Editing a proxy host without the UI

No API credentials needed if you're on casaos: update NPM's SQLite through the container's own node + knex,
then make the **same** change in the generated `data/nginx/proxy_host/<id>.conf` and reload. Both have to change:
the conf is what nginx serves, and the DB is what the UI re-renders from on the next save. Verified 2026-10-30 (host 21):
```
sudo cp -p /footage/services/nginxIntern/data/database.sqlite{,.bak-<why>}
sudo docker exec -w /app nginxIntern node -e '
const k=require("knex")({client:"sqlite3",connection:{filename:"/data/database.sqlite"},useNullAsDefault:true});
k("proxy_host").where({id:21}).update({forward_host:"192.168.11.21"}).then(n=>{console.log(n);return k.destroy()})'
sudo sed -i 's/set $server         "OLD";/set $server         "NEW";/' /footage/services/nginxIntern/data/nginx/proxy_host/21.conf
sudo docker exec nginxIntern nginx -t && sudo docker exec nginxIntern nginx -s reload
```
There's no `sqlite3` CLI on casaos or in the container; the knex route is the way.

## Proxy hosts that point off-casaos
- **18 `ha.intern.dgmneto.com` → `192.168.11.21:8123`** (homelab-notebook, since 2026-10-31; was docker DNS `homeassistant`).
  HA sees these requests from **`192.168.11.13`** (this container egresses via the docker bridge, NATed to the casaos host
  IP), so that's what HA's `trusted_proxies` must contain. Pre-change DB copy: `data/database.sqlite.bak-pre-ha-move`.
- **21 `z2m.intern.dgmneto.com` → `192.168.11.21:8080`** (homelab-notebook, since 2026-10-30). Pre-change DB copy:
  `data/database.sqlite.bak-pre-z2m-move`.

## Quirks / runbook

- This is the **internal** twin of `nginxProd` (`192.168.14.33`). The two are
  identical images differing only by IP and intended scope. Add LAN-only hosts
  here; add public hosts to `nginxProd`.
- Same `/footage` storage dependency and macvlan host-unreachability caveat as
  `nginxProd`.
- Restart policy `always`.
