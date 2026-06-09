# gluetunProtonVPN

VPN gateway container. Establishes a ProtonVPN WireGuard tunnel and acts as the
network namespace for other containers that must route ALL their traffic through
the VPN (notably `qbittorrent`). Also handles ProtonVPN port forwarding so
inbound torrent connections work.

## VPN routing (IMPORTANT)

- `qbittorrent` runs with `network_mode: container:gluetunProtonVPN`. It has **no
  network stack of its own** — it shares gluetun's namespace. Every byte of
  qbittorrent traffic exits through the ProtonVPN tunnel.
- **If gluetun is down or restarting, qbittorrent loses all network.** qbittorrent
  cannot start before gluetun, and a gluetun restart drops qbittorrent's
  connectivity until gluetun is healthy again.
- qbittorrent's WebUI port **9090** is exposed inside gluetun's namespace, not on
  qbittorrent. The Nginx Proxy Manager upstream for qbittorrent therefore points
  at host `gluetun`, port `9090` (see Integrations).
- Same pattern applies to `prowlarr` (proxied via `gluetun:9696`) — it also rides
  the gluetun namespace.

## Image

- `qmcgaw/gluetun:latest` — **unpinned `:latest`** (running digest
  `sha256:5665416a97ad2823dda6986a581b8913cc3af1b196ac768f5130abad4b0d4f62`).

## VPN configuration

- Provider: ProtonVPN
- Protocol: WireGuard
- Port forwarding: enabled (ProtonVPN VPN port forwarding, with an up-command hook
  to push the forwarded port into qbittorrent)
- `.env` keys (values intentionally NOT recorded here — contain the WireGuard
  private key):
  - `VPN_SERVICE_PROVIDER`
  - `VPN_TYPE`
  - `WIREGUARD_PRIVATE_KEY` (secret)
  - `SERVER_COUNTRIES`
  - `PORT_FORWARD_ONLY`
  - `VPN_PORT_FORWARDING`
  - `VPN_PORT_FORWARDING_UP_COMMAND`

## Access

No host ports are published (`PortBindings` is empty). Internal-only container
ports: `8000` (gluetun control server), `8888` (HTTP proxy), `8388` tcp/udp
(Shadowsocks), `1080` (SOCKS). Reach dependent service WebUIs via Nginx Proxy
Manager (internal), which dials the `gluetun` hostname on the internal network.

## Paths

- Compose (server): `/home/dgmneto/homelab/services/gluetunProtonVPN/compose.yaml`
- Config / secrets: `.env` alongside the compose file
- No bind-mounted config dir under `/footage` for this service.

## Networks

- `internalNetwork` (external Docker network, alias `gluetun` / `gluetunProtonVPN`).
  Runtime IP observed: `172.21.0.3`.
- `cap_add: NET_ADMIN` required to manage the tunnel interface.

## Integrations

- **qbittorrent** — shares this namespace (`network_mode: container:`), WebUI on
  `gluetun:9090`.
- **prowlarr** — shares this namespace, WebUI on `gluetun:9696`.
- **Nginx Proxy Manager (nginxIntern)** proxy hosts pointing at `gluetun`:
  - `qbittorrent.intern.dgmneto.com` -> `gluetun:9090`
  - `prowlarr.intern.dgmneto.com` -> `gluetun:9696`
  - `testvpn.intern.dgmneto.com` -> `gluetun:80`

## Quirks / runbook

- `restart: always`.
- Dependent containers (qbittorrent, prowlarr) must be restarted after gluetun
  restarts if they fail to recover networking.
- To verify the tunnel is up: `testvpn.intern.dgmneto.com` (proxies gluetun:80) or
  query the control server on port `8000` from inside the internal network.
- NEVER commit `.env` — it holds the WireGuard private key.
