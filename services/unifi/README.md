# UniFi (network: UDR gateway, switches, APs)

Not a homelab-hosted service: the UniFi Network app runs **on the UDR** ("3E House", `192.168.11.1`,
UniFi OS 6.0.x), cloud-managed via unifi.ui.com. Site `default` ("Default"). Facts below read from the API on
2026-11-11.

## API access (agents)

- **Key:** env var `UNIFI_API_KEY` in Claude cloud sessions = a **Site Manager (cloud) key** (unifi.ui.com → API).
  It authenticates against `https://api.ui.com/v1/...` (`hosts`, `sites`, `devices`).
- **Local API is unreachable from cloud sessions:** `https://192.168.11.1/proxy/network/...` → 403 from the agent
  proxy ("Destination IP is in a private/reserved range"), even though Tailscale routes .11. Don't retry it.
- **Use the cloud connector instead** — full read access to the Network app, both legacy and v2 endpoints:
  `https://api.ui.com/v1/connector/consoles/<host id>/proxy/network/<path>`. Wrapped in
  [`tools/unifi.sh`](tools/unifi.sh) (looks up the host id, redacts secrets):
  ```
  services/unifi/tools/unifi.sh api/s/default/stat/sta | jq '.data[] | {hostname, ip, network, sw_mac, sw_port, wired_rate_mbps, essid}'
  ```
- **Gotcha — secrets in responses:** `api/s/default/rest/setting` (key `mgmt`) returns the **device SSH username/password
  in clear**, plus API tokens; `connectivity` returns the mesh PSK; `wlanconf` returns `x_passphrase`. Never write raw
  dumps into the repo/logbooks; the helper redacts `x_*`/`*passw*`/`*token*`/`*psk*` by default.
- Only GETs have been used. Writes through the connector are possible but untested — ask the user first.

## Topology (2026-11-11)

| Device | Model | IP | Uplink |
|---|---|---|---|
| 3E House (gateway/console) | UDR | 192.168.11.1 (WAN 217.155.23.76) | WAN = Zen (DHCPv6-PD) |
| Main Switch | USW Lite 8 PoE | 192.168.11.71 | UDR port 1, 1 G |
| Office (in-wall AP + 4-port switch) | U6 IW | 192.168.11.221 | Main Switch port 2, 1 G |
| Loft Bedroom | U7 Pro Wall | 192.168.11.244 | Main Switch port 3, 1 G |
| **Tv unit** | USW Flex Mini | 192.168.11.51 | **Main Switch port 1 ↔ Flex port 1 at 100 Mbps** (see below) |
| Front garden camera | G6 Turret (Protect) | 192.168.11.14 | — |

Wired clients of interest: `casaos` `.13` → Office port 3 (1 G); `homelab-notebook` `.21` → Office port 4 (1 G);
**Apple TV "Living-Room"** `.236` (MAC `c4:f7:c1:12:02:5f`) → Tv unit port 5 (1 G, DHCP, no reservation).
Main Switch ports 6/7 carry the `WAN` VLAN 2 (ISP handoff via the switch).

### Known issue: Tv unit uplink at 100 Mbps
The Flex Mini's uplink (Main Switch port 1 ↔ Flex port 1) and Flex ports 2–4 (incl. Chromecast) negotiate at
**100 Mbps full duplex**, 0 errors. Everything behind the Tv unit — including the Apple TV — is capped at ~94 Mbps:
this is the ceiling seen in the 2026-11-04 Plex investigation. Most likely cause: the cable (or a keystone/patch)
between Main Switch port 1 and the Tv unit has only 2 working pairs. Fix: re-terminate/replace that cable, then check
`unifi.sh api/s/default/stat/device | jq '.data[]|select(.name=="Tv unit").uplink.speed'` → 1000. Ports 2–4 at 100
may just be 100 Mbps devices.

### Known issue: RAs sourced from the GUA after the 2026-11-11 auto-update (breaks Matter/Thread)
Overnight auto-update (daily 03:00, apps included): firmware **5.1.35 → 6.0.17** (04:02:59 UTC), Network **10.6.109 → 11.0.99**
(04:17:23 UTC). Since then the RA on Default comes from `2a02:8012:882b::1`, not `fe80::7a45:58ff:feb1:a57d` (which stopped
answering ND). RFC 4861 hosts ignore it → no IPv6 default route on LAN hosts, and the Apple TV (Thread BR) can't route back to
LAN GUAs → every tado/Matter node unavailable in HA from 06:27. Network IPv6 settings are unchanged. Runbook:
[services/matter/README.md](../matter/README.md). Event history: POST `v2/api/site/default/system-log/all` with
`{"timestampFrom":<ms>,"timestampTo":<ms>,"pageSize":200,"pageNumber":0}` (the legacy `stat/event` returns 404 on Network 11).

## Networks

| Network | VLAN | Subnet | IPv6 |
|---|---|---|---|
| Default | untagged | 192.168.11.0/24 | Prefix delegation, SLAAC, RA on (priority high) → `2a02:8012:882b::/64` |
| Docker - public | 14 | 192.168.14.0/24 | static, SLAAC |
| Docker - IPv6 | 15 | 192.168.15.0/24 | static, SLAAC |
| 3E Home | — | 192.168.1.0/24 | remote-user VPN |
| Zen (WAN) | — | — | DHCPv6, prefix delegation |

IGMP snooping **off** on all networks (multicast floods — fine for mDNS/Matter). mDNS reflector on for Default + both
Docker VLANs (`setting.mdns` mode `all`).

## Wi-Fi

Both SSIDs map to **Default** (no IoT VLAN): `Amora’s` (2.4/5/6 GHz, WPA2/WPA3 transition, fast roaming) and
`Amora’s IoT` (2.4 GHz only, WPA2, PMF off). Neither has client isolation (`l2_isolation=false`); multicast
enhancement off; no ACL device isolation in `global_switch`.

## Firewall

Zone-based. All 82 policies are **predefined** (no custom rules, no legacy `firewallrule`s, no traffic rules).
Internal zone = Default + Docker VLANs (all allowed between each other). External → Internal: block all + block
invalid, **both IPv4 and IPv6** — so unsolicited inbound IPv6 to LAN hosts is blocked at the gateway (config-level
verification; not tested from outside). See [notes/lan-ipv6.md](../../notes/lan-ipv6.md).
