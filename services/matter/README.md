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
- **"All tado unavailable at once" runbook (incident 2026-11-11 06:27–06:29).** All 6 nodes dropped within 2 min and
  stayed down with `CASESession timed out`. Check in this order (all read-only, from a cloud session):
  1. `tools/nodes.py` → every `avail=False` means a shared path, not one device.
  2. `tools/browse.py` (run it with **matter-server's** env: `{ sed -n 3p <.matter-server-wrapped>; cat browse.py; }`. HA's
     python no longer has zeroconf on its path after the 11-10 deploy). Apple `_meshcop` with `sb=…fb1` = BR up. The devices'
     `BFABFD88F60E01A6-…` `_matter._tcp` records are visible even while down: the SRP lease is cached by the BR, so
     **seeing the record ≠ reachable**.
  3. `ping -6 fde9:b6c5:757:0:<iid>` for those addresses. 100 % loss from homelab-notebook **and casaos** while
     `ping -6 fe80::67:28bc:f5ae:b3b6%enp2s0` works = traffic dies at/behind the Apple TV, not in HA or the NixOS firewall
     (replies to our pings are ESTABLISHED and accepted).
  4. `tools/ra.py`. On 11-11 the UniFi (MAC `78:45:58:b1:a5:7d`) sent its RA from **`2a02:8012:882b::1`, not link-local**
     (on 11-06 it was `fe80::7a45:58ff:feb1:a57d`; that neighbour is now FAILED). RFC 4861 hosts drop the router part, so
     **no IPv6 default route on any Linux box**; NetworkManager still installs the on-link /64. **User confirmed 11-11: devices online in the tado app and Apple Home**, so the Thread mesh/BR is fine. The break is
     the LAN↔BR IP path: the Apple TV doesn't answer on its GUA either, i.e. it no longer treats `2a02:8012:882b::/64` as on-link
     (it also ignores the GUA-sourced RA), so it drops replies to HA's GUA. Root cause = the UniFi RA change (Apple Home/tado
     cloud don't need LAN IPv6, so they keep working). Next steps (user, on site): check whether the devices are online in the
     **tado app / Apple Home** (yes → IP path; no → Thread/BR), restart the Apple TV, and check the UniFi for an overnight
     update and its IPv6 settings on the Default network. matter-server retries every 60 s and recovers by itself.
  - **Cause found 2026-11-11 (UniFi API):** overnight UDR auto-update, firmware 5.1.35 → 6.0.17 (04:03 UTC) + Network
    10.6.109 → 11.0.99 (04:17 UTC); since then the RA is GUA-sourced. Check with
    `services/unifi/tools/unifi.sh` + the `system-log/all` POST in [services/unifi](../unifi/README.md); confirm with `tools/ra.py`.
    Fix = get the UDR sending RAs from link-local again (restart; else toggle IPv6 on Default; else report/rollback). Recovery check:
    `tools/ra.py` shows `RA from fe80::7a45:58ff:feb1:a57d`, then `tools/nodes.py` all `avail=True` within a few minutes.
  - **Resolved 2026-11-11 12:53 UTC by restarting the UDR**: RA back from `fe80::7a45:58ff:feb1:a57d`, v6 default route back,
    nodes 3/7/9/10 recovered by themselves within a minute.
  - **Gotcha — matter-server gives up after 30 min:** `<Node:N> Node setup not completed after 30 minutes, giving up.` After
    that it never retries that node, even once the path is fixed (node 2 stayed down). Fix: `sudo systemctl restart matter-server`
    (all nodes drop ~1 min, then resubscribe). Do this as the last step of any long outage.
  - **matter-server only sets up nodes it sees on mDNS** (`<Node:N> Discovered on mDNS` → `Setting-up node`). A node with no
    `_matter._tcp` record (node 8 on 11-11) gets no log lines at all; that's a device/Thread-side problem (battery, dropped off
    the mesh, SRP not re-registered): wake/check it in the tado app; it gets set up automatically once it advertises again.
  - **Reading the `_matter._tcp` list:** each device publishes one record *per fabric* (`<compressed fabric id>-<node id>`), all on
    the same Thread host name/address. Fabrics seen 2026-11-11: `BFABFD88F60E01A6` = HA, plus `2352D62C1A7D8359`,
    `356911195B19D07B`, `95FF102CF4A68F57` (Apple Home / tado / one more; node 10 lacks `95FF…`). Group by host name to count
    physical devices. At 13:10 only **5 Thread hosts** existed: node 8 (Small Room TRV) had **no record on any fabric**, i.e.
    not just missing from HA but not reachable via the BR at all, even though Apple Home / tado still listed it.
  - Gotcha: `ip -6 route | grep -E "fde9|default"` hides the on-link `2a02:…/64` route. Use plain `ip -6 route`.
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
