# matter (matter-server)

Python Matter Server — bridges Matter/Thread devices to Home Assistant over a websocket. HA's Matter integration drives commissioning and control through this server.

> **Moved 2026-10-30 to homelab-notebook** (NixOS `services.matter-server`, `hosts/homelab-notebook/nixos/home-automation.nix`):
> `ws://192.168.11.21:5580/ws` (HA's matter entry points here). State `/var/lib/private/matter-server` (DynamicUser),
> PAA certs `/var/cache/private/matter-server/certs`, logs `journalctl -u matter-server`. **Must run with
> `--vendorid=65521`** (the fabric's admin was created under 0xFFF1; the module default 4939 crashes it).
> `--primary-interface=enp2s0`, firewall 5580/tcp + 5353/udp. 0 devices at the move (fabric kept); **6 tado° X nodes since 2026-11-09**, see "Commissioned devices" below. casaos container removed; pre-move copy `/footage/services/matter/data.bak-pre-move-20261030`.
> **Thread (2026-11-06):** the only Thread border router is the **Apple TV 4K gen 3 `192.168.11.236`** (Apple network
> `MyHome1662126353`, OMR `fde9:b6c5:757::/64`); HA holds **no** Thread dataset (fine for multi-admin). CHIP operational
> UDP port is **ephemeral** (e.g. 47870) and not opened in the NixOS firewall — see the tado° X audit
> [TADO-X-READINESS.md](TADO-X-READINESS.md) for the staged (log → accept) UDP rule scoped to `enp2s0` + `fde9:b6c5:757::/64` and the reusable mDNS/RA
> diagnostics + firewall drift check in [tools/](tools/). **Gotcha:** `systemctl show -p MainPID matter-server` is the
> start-script wrapper; the socket owner is its child: use the unit's cgroup PIDs with `sudo ss -uapn` (no `avahi`/`tcpdump` on the box; they run on HA's own python + zeroconf).
> Below the device table = the old casaos setup.

## Commissioned devices (server truth 2026-11-10)
All tado° X, Matter-over-Thread via the Apple TV BR, commissioned 2026-11-09 by multi-admin share (tado app → HA).
Re-dump any time with [`tools/nodes.py`](tools/nodes.py) (matter-server websocket, read-only).

| Node | HA device (area) | Model | fw | climate entity |
|---|---|---|---|---|
| 2 | Living Room Thermostat (Living room) | Smart Thermostat X | 1.4.289 | `climate.living_room_living_room_thermostat` |
| 3 | Hall Thermostat (Entry hall) | Smart Thermostat X | 1.4.289 | `climate.smart_thermostat_x` |
| 7 | Guest Room TRV (Guest room) | Smart Radiator Thermostat X | 1.4.289 | `climate.smart_radiator_thermostat_x` |
| 8 | Small Room TRV (Little room) | Smart Radiator Thermostat X | 1.4.289 | `climate.little_room_small_room_trv` |
| 9 | Office TRV (Office) | Smart Radiator Thermostat X | 1.4.289 | `climate.smart_radiator_thermostat_x_2` |
| 10 | Loft Bedroom TRV (Loft bedroom) | Smart Radiator Thermostat X | **1.0** | `climate.loft_bedroom_loft_bedroom_trv` |

Node IDs 4–6 were burned by failed attempts (4: `0x7E` "NOC for a fabric that already exists" = device already on
HA's fabric; 5/6: timeouts). Per device HA gets: `climate` (heat-only Thermostat cluster 513, `heat`/`off`), temperature,
humidity, a **binary** battery sensor (BatChargeLevel only, no %), 1–2 identify buttons; reboot count/uptime/boot reason
are disabled by the integration.
**Gotchas:**
- **Fresh TRVs arrive on fw 1.0 (swNum 64) and tado updates them to 1.4.289 itself** (not via Matter OTA: no OTA
  requestor cluster). The 1.0 layout differs: humidity on endpoint 1, no PowerSource (no battery entity), no serial,
  no ICD cluster. After the update HA adds the new entities but **leaves the ep-1 humidity sensor frozen at its last
  value** (`sensor.little_room_small_room_trv_humidity` stuck since 23:21 on 11-09, while `..._humidity_2` is live).
  Delete it in HA. Node 10 will do the same after it updates.
- **Don't bridge them back to Apple Home**: they are already native there. HA's HomeKit Bridge no longer exports
  `climate` (2026-11-10) because that showed every device twice.
- Entity IDs are inconsistent (some generic `smart_radiator_thermostat_x_2`, some with a doubled area prefix). Rename in
  HA (Settings → Entities) before writing automations; the Home dashboard references the current IDs, and renaming
  through the UI updates them.
- Flapping seen only on node 10 (Loft, farthest from the Apple TV, still on fw 1.0): 2× "Marked node as unavailable"
  23:44 and 23:59 on 11-09, CASE timeouts (controller-initiated, so **not** the inbound-conntrack firewall case in
  TADO-X-READINESS), recovered by 00:02. Quiet since. Coverage / pending firmware; watch it.

### Zigbee devices these replaced (all removed 2026-11-10)
Matched by area plus timing. **Removed from z2m, and their HA automations deleted, 2026-11-10** (see the homeassistant README); table kept for history.
| New (Matter node) | Old z2m device (friendly name, IEEE) | Status at 00:35, before removal |
|---|---|---|
| Office TRV (9) | `Office/TRV Valve` AVATTO TS0601 `0xa4c138c24997bf89` | still reporting (battery) |
| Small Room TRV (8) | `Little Room/TRV Valve` AVATTO TS0601 `0xa4c138568aeec433` | still reporting |
| Guest Room TRV (7) | `Guest Bedroom/TRV Valve` AVATTO TS0601 `0xa4c138cc9ea0e43d` | still reporting |
| Loft Bedroom TRV (10) | `Loft Bedroom/TRV Valve` AVATTO TS0601 `0xa4c13868ef0d6c52` | still reporting (LQI 84) |
| Hall Thermostat (3) | `Hall/Thermostat` Shelly 1 Mini Gen 4 relay `0x7c2c67fffe73e89c` (`switch.hall_thermostat`) | last seen 11-09 17:47 → presumably removed |
| Living Room Thermostat (2) | `Dining Room/Thermostat` Bosch Room thermostat II 230V `0x001e5e0902ba15d2` (*inferred*: other area, but last seen 11-09 15:00, node 2 commissioned 15:25) | gone |

The HA automations, `zoned_heating` entry and template helper that used them were deleted 2026-11-10. The tado devices have
no calibration entity over Matter; tado does that itself.

## casaos setup (historical)

## Image
`ghcr.io/matter-js/python-matter-server:stable` (`stable` channel — moving tag, not a fixed version)

## Access
- Websocket: `5580/tcp` → `ws://<host>:5580/ws`
- IPs: macvlan(IPv6 net) `192.168.15.25` / `fd00:2::25`, internal `172.21.0.95`
- HA connects to `ws://192.168.15.25:5580/ws`.

## Paths
- Container name: **`matter-server`** (not `matter`: `docker exec matter-server …`). Version 8.1.2 (2026-10-30).
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
