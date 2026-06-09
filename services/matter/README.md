# matter (matter-server)

Python Matter Server — bridges Matter/Thread devices to Home Assistant over a websocket. HA's Matter integration drives commissioning and control through this server.

## Image
`ghcr.io/matter-js/python-matter-server:stable` (`stable` channel — moving tag, not a fixed version)

## Access
- Websocket: `5580/tcp` → `ws://<host>:5580/ws`
- IPs: macvlan(IPv6 net) `192.168.15.25` / `fd00:2::25`, internal `172.21.0.95`
- HA connects to `ws://192.168.15.25:5580/ws`.

## Paths
- Compose: `/home/dgmneto/homelab/services/matter/compose.yaml`
- Data: `/footage/services/matter/data` → `/data` (Matter fabric/credentials)

## Networks / devices
- Networks: `macVlanIPv6Network` (mapped as `macvlan` here) + `internalNetwork`. **Not** `network_mode: host` — it uses the macvlan with IPv6.
- `security_opt: apparmor=unconfined`.
- No USB/serial device passthrough.

## Integrations
- **HA ← matter-server:** HA's Matter integration connects to the websocket above. matter-server handles Matter device commissioning and Thread/Wi-Fi Matter control; HA does not talk to Matter devices directly.

## Quirks / runbook
- Matter relies heavily on IPv6 / mDNS multicast. It is intentionally on the **IPv6 macvlan** (`fd00:2::25`) so it can reach Matter/Thread devices on the LAN — a plain bridge network would break discovery. If commissioning fails, suspect IPv6/mDNS reachability between this container and the device's network, not the container itself.
- `apparmor=unconfined` is required for the Matter SDK's networking.
- Fabric credentials live in `/footage/services/matter/data` — losing this volume means re-commissioning every Matter device. `/footage` full can corrupt this state.
- `stable` is a moving tag; a Watchtower pull can bump the Matter SDK and require a matching HA core version.
