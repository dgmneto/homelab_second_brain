# Logbook — matter

Reverse-chronological. Newest entry on top. One entry per task that touches **matter** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-28 15:35 — tado app shows no devices (Apple Home OK): Apple TV BR dead, NAT64 only on the Apple TV
Decoded Thread network data (`/diagnostics` → `NetworkData`, no keys in it): `::/0` has-route from both 0x7000 (Apple TV) and 0xf800 (MR5U).
**NAT64 prefix `fde9:b6c5:757:ffff::/96` only from the Apple TV** (flags 0xf0). OMR `fde9:b6c5:757::/64` from the Apple TV. SRP anycast+unicast from the Apple TV.
BBR primary = MR5U. Test: removed the metric-50 MR5U pin, `PUT /node/state "disable"` on the MR5U, pinned the route via the Apple TV → **6/6 nodes 100 % loss after 150 s**.
So the Apple TV doesn't forward LAN→Thread at all while Tailscale (still online on the tailnet) runs on it. The MR5U had been carrying all of HA's traffic.
Re-enabled the MR5U (router in 60 s) and re-pinned via the MR5U → 6/6 0 % loss, all avail=True in HA. Explains the symptoms: Apple Home uses the Apple TV's own radio (works); the
tado app goes through tado's cloud ← NAT64 on the Apple TV (broken). **Correction to the 15:25 entry:** the "/128 via the Apple TV, 6/6 ping OK" test was invalid. The Apple TV
bounced those packets back over the LAN to the MR5U (it also learns the MR5U's RIO). Only a test with the MR5U's Thread disabled proves the Apple TV path.
Open: the user must disconnect/delete Tailscale on the Apple TV and restart it. Then remove the metric-50 route.

## 2026-11-28 15:25 — Apple Home + tado app can't reach the tado devices, HA fine (investigation)
`tailscale status`: `apple-tv` still **online** (VPN connected; the iPhone is not on the tailnet). Path into Thread via the Apple TV now works (6/6 pings with a temporary /128 route via
`fe80::189f:c96:5398:f346`), so the inbound loop from 01:42 is gone. The hub's own controller traffic can't be observed from here.
Thread is healthy: one partition (leader Apple TV, id 28), 2 routers. Network data has only the Apple OMR `fde9:b6c5:757::/64`; the MR5U's `_meshcop` `omr` TXT
`fd19:d69c:fe9c:1::/64` is an unused local candidate, not published. Children: Apple TV 4, MR5U 2. The MR5U holds ALOCs fc38 (primary BBR) + fc10 (service).
All 24 `_matter._tcp` records resolve to fde9 addresses on the LAN.
**Fabric tables (read_attribute 0/62/1 with `fabric_filtered: false`; the cached attribute is fabric-filtered):** vendor 4996 = Apple Keychain, 4942 = tado,
4937 = Apple Home (label "3E"), 65521 = HA ("Casa"). All 6 have the Apple Home + HA fabrics. **Nodes 8 (SmallRoomTRV) and 10 (LoftTRV) have no tado fabric**, so the
tado app can't see those two at all until they're re-shared to tado (multi-admin pairing code from Apple Home or HA).
Conclusion: the Thread side is fine. Most likely the Apple TV hub is still impaired by its active Tailscale VPN (same as 11-14). Asked the user to disconnect it and reboot the Apple TV.
Next isolation step if that fails: `PUT /node/state "disable"` on the MR5U for a test.

## 2026-11-28 — 4/6 tado unavailable again: Tailscale on the Apple TV (stopgap route via MR5U)
User re-enabled Tailscale on the Apple TV (`apple-tv` online in the tailnet). matter-server: nodes 2, 3, 9, 10 avail=False, retrying setup.
`ping -6` showed `Time exceeded` from `2a02:8012:882b::1`, and tracepath looped Apple TV ↔ UniFi (same as 11-14). It was partial because the ECMP OMR route sends half the traffic via the MR5U.
Added `ip -6 route add fde9:b6c5:757::/64 via fe80::90da:72ff:fefa:b910 dev enp2s0 metric 50` → 6/6 at 0 % ping loss. Restarted matter-server → all 6 avail=True
after ~100 s. Open: the user must turn Tailscale off on the Apple TV (tado app/Apple Home still broken), then delete the metric-50 route.

## 2026-11-24 — Second Thread BR (SLZB-MR5U) joined; before/after pings
No matter-server change. SLZB-MR5U OTBR joined Apple's Thread network as router/BR; homelab-notebook now routes `fde9:b6c5:757::/64`
via both BRs (ECMP). Baseline 7-day counts: 35 unavailable, 263 liveness timeouts, 2200 CASE timeouts. See [../thread](../thread/README.md).

## 2026-11-15 — Root cause: Tailscale on the Apple TV
User had enabled Tailscale on the Apple TV (Thread BR) ~2026-11-14 19:00. After they turned it off (tailnet shows `apple-tv` offline), `ping -6` to node addresses works and nodes 2,3,7,8,9,10 all logged `Subscription succeeded` by 12:51. Documented as the first thing to check (matter + tailscale READMEs).

## 2026-11-15 — All tado° X nodes unavailable: Apple TV ↔ UniFi routing loop
Investigation, no change. At 2026-11-14 19:00–19:04 every node (2,3,7,8,9,10) hit subscription/CASE timeouts and
has been retrying since. mDNS (`tools/browse.py`) still shows the Apple TV BR + all nodes' `_matter._tcp` records;
route `fde9:b6c5:757::/64 via fe80::67:28bc:f5ae:b3b6` (Apple TV) present; Apple TV pingable. But
`ping -6` to node addresses → `Time exceeded: Hop limit` from `2a02:8012:882b::1`; `tracepath -6` loops Apple TV ↔
UniFi. Conclusion: the Apple TV stopped forwarding into Thread. Recommended fix to the user: restart the Apple TV.
Runbook added to README.

## 2026-11-11 — Node 8: online on Thread, SRP registration missing
User: Small Room TRV responds in Apple Home (setpoint change triggered heating). Direct DNS-SD lookup of
`BFABFD88F60E01A6-0000000000000008._matter._tcp` from homelab-notebook → no answer (node 2 resolves fine). So the device is on
the mesh but has no SRP/DNS-SD registration at the Apple TV; Apple Home/tado don't need it, matter-server does. Advised a
battery reseat. Read-only.

## 2026-11-11 — Small Room TRV (node 8): not advertised on any fabric
User: it shows in tado and Apple Home. mDNS browse (tools/browse.py) at ~13:10: 21 `_matter._tcp` records, grouped by Thread
host = 5 devices, each on HA fabric `BFABFD88…` plus 2–3 other fabrics (Apple/tado). Node 8 has no record on **any** fabric,
so it is not registered with the Apple TV BR at all; Apple Home/tado likely show a cached tile. Asked the user to test it
(change setpoint → reacts / "No Response"), then reseat batteries to force a Thread rejoin. Read-only.

## 2026-11-11 — UDR restart fixed the RA; 5/6 tado nodes back
User restarted the UDR ~12:51 UTC. Polled `tools/ra.py` from homelab-notebook: offline 12:52–12:53, at 12:53:54 RA from
`fe80::7a45:58ff:feb1:a57d` again; v6 default route back, `curl -6 ipv6.google.com` 200. Nodes 3/7/9/10 resubscribed by
12:53:52 on their own. Node 2 had hit matter-server's "giving up after 30 minutes" (11:17) and never retried →
`sudo systemctl restart matter-server` on homelab-notebook at 12:59; node 2 back 13:00. **Node 8 (Small Room TRV) still
down**: no `_matter._tcp` record on mDNS since the morning, so matter-server never tries it; device/Thread side, needs a
check in the tado app. Runbook gotchas added to services/matter/README.md.

## 2026-11-11 — tado outage: trigger = overnight UDR auto-update (UniFi API)
Read-only, via `UNIFI_API_KEY` + the Site Manager connector. UniFi system log: UDR firmware 5.1.35 → 6.0.17 at 04:02:59 UTC
and UniFi Network 10.6.109 → 11.0.99 at 04:17:23 UTC (auto-update daily 03:00). Default IPv6 settings unchanged (PD, SLAAC,
RA on). Re-checked 12:45: `tools/ra.py` still shows the RA from `2a02:8012:882b::1`; `tools/nodes.py` all 6 nodes
`avail=False`; homelab-notebook still has no v6 default route. Nothing changed on the gateway; restart proposed to the user.

## 2026-11-11 — UniFi controller checked via API (closes tado X audit UniFi items)
Read-only. `UNIFI_API_KEY` is a Site Manager key: `api.ui.com/v1/{hosts,sites,devices}` → 200; local `https://192.168.11.1`
→ 403 from the agent proxy (private IP). Full Network-app reads work through the cloud connector
`api.ui.com/v1/connector/consoles/<id>/proxy/network/...`; wrapped in `services/unifi/tools/unifi.sh` (redacts secrets —
`rest/setting` returns the device SSH password in clear; raw dumps deleted). Findings: Apple TV `.236` (Tv unit Flex Mini
port 5) and homelab-notebook `.21` (Office U6 IW port 4) wired on **Default**; both SSIDs on Default, no client
isolation, IGMP snooping off, mDNS reflector on; Default IPv6 = PD + SLAAC; firewall = 82 predefined zone policies only,
External→Internal blocked v4+v6. **Root cause of the ~94 Mbps Apple TV ceiling: Tv unit uplink (Main Switch port 1)
negotiates at 100 Mbps** (0 errors) — likely a 2-pair cable. TADO-X-READINESS UniFi row now PASS; new services/unifi
README; lan-ipv6 note, Plex runbook, CLAUDE.md updated. Nothing changed on the network.

## 2026-11-11 — tado outage narrowed to the UniFi RA change
User: all devices online in the tado app and Apple Home, so Thread is fine. HA's path fails because the Apple TV no longer answers on
or routes back to `2a02:8012:882b::/64`, after the UniFi started sending RAs from its GUA. Asked the user to restart the UniFi gateway
and check for an overnight update / IPv6 settings. No change on the box.

## 2026-11-11 — Investigation: all tado nodes unavailable since 06:27
Read-only, except one temporary on-link route on homelab-notebook, removed right after (it was already there via RA). All 6 nodes
`avail=False` since 06:27–06:29; matter-server retries CASE every 60 s and times out. The Apple BR is up (`sb` 0fb1, leader),
and 5/6 nodes' `_matter._tcp` records resolve to `fde9:b6c5:757::…` (node 8 not advertised), but pings to them are 100 % lost
from homelab-notebook and casaos. The Apple TV's link-local answers in 1 ms. The UniFi now sends its RA from its GUA
`2a02:8012:882b::1` (link-local gone), so there's no IPv6 default route LAN-wide. Root cause is either that or the Apple TV BR.
Needs on-site checks (tado app, Apple TV restart, UniFi). Runbook added to README.

## 2026-11-10 — Old Zigbee heating removed; dashboard uses the tado entities
The z2m devices these replaced were removed, and the HA heating automations deleted. The Home dashboard now shows the 6 tado
climate entities. See the homeassistant and z2mqtt logbooks.

## 2026-11-10 — Matched the tado° X devices to the Zigbee devices they replace
Read-only. 4 AVATTO TRVs ↔ 4 tado TRVs by area (old ones still online); Shelly Hall relay ↔ Hall Thermostat;
Bosch Dining Room thermostat ↔ Living Room Thermostat (inferred from timing). Listed HA automations still bound to the old
devices. Table in README.

## 2026-11-10 — Check of the new tado° X devices in HA
Read-only. 6 nodes commissioned 2026-11-09 15:25–23:36 (2 Smart Thermostat X, 4 Smart Radiator Thermostat X; node IDs
2,3,7,8,9,10; 4–6 failed: NOC-exists / timeouts). At 00:30 all 6 `available`, all HA entities reporting. Node 10 (Loft
TRV) still fw 1.0 (others 1.4.289), flapped twice 23:44/23:59 (CASE timeouts) then stable from 00:02. Node 8 shows the
fw 1.0 → 1.4.289 transition leaves a frozen ep-1 humidity entity in HA. Sources: `journalctl -u matter-server`, ws
`get_nodes`, HA `.storage` registries + recorder DB (read-only sqlite). Added `tools/nodes.py`; README device table.

## 2026-11-06 — tado° X audit: firewall plan finalised (second review)
Read-only. `matter-server --help` (8.1.2): no option to pin the CHIP UDP port (`--port` = TCP websocket). Unit:
DynamicUser, empty CapabilityBoundingSet; `ip_unprivileged_port_start` 1024. Gotcha found: MainPID is the start
wrapper, the socket owner is its child, so match `sudo ss -uapn` against the unit's cgroup PIDs. Plan now: a Stage-1
LOG rule plus a passive /proc/net/nf_conntrack snapshot, with 4 correlation criteria (DPT, DST, tuple-expiry timing,
symptom). Stage 2 accepts `-i enp2s0 -s fde9:b6c5:757::/64 -p udp --dport 1024:65535`, with no dependence on
ip_local_port_range. Added `services/matter/tools/matter-fw-check.sh` (drift check); ran it read-only on the box:
exit 0 on the real state, 3 WARNs on planted mismatches. Nothing deployed.

## 2026-11-06 — tado° X audit: firewall recommendation narrowed after review
User pushed back on the `fc00::/7` accept rule as too broad. Read-only checks on homelab-notebook: refused packets aren't
logged (no LOG in `nixos-fw-log-refuse`), `/proc/net/nf_conntrack` readable, ephemeral ports 32768–60999, rpfilter on.
New recommendation: stage a log-only rule, then (only if drops seen) accept `-i enp2s0 -s fde9:b6c5:757::/64 -p udp
--dport 32768:60999`; conntrack timeout bump only as complement; prefix-drift check documented. Nothing deployed.

## 2026-11-06 — Audit: network readiness for tado° X (Matter-over-Thread via Apple TV)
Read-only (no service change). Via `ssh claude@homelab-notebook` / `claude@casaos`: `ip addr/route/neigh`, NM, ip6tables, `ss`, journals,
HA `.storage` (config entries + device registry, no datasets/secrets), passive mDNS browse with HA's python-zeroconf and
one Router Solicitation (`services/matter/tools/{browse,ra}.py`). Findings: sole Thread BR = Apple TV 4K gen 3
(`AppleTV14,1`, tvOS 27.2) `192.168.11.236`, active leader/BBR, RIO `fde9:b6c5:757::/64` routed on homelab-notebook;
HA matter/thread entries healthy, 0 Matter nodes, no HA Thread dataset; UniFi no longer advertises ULA `fd00::/64`
(notes/lan-ipv6.md corrected); no HA/matter containers on casaos. No blockers; suspected: ephemeral CHIP UDP port not
in NixOS firewall, single BR, stale fd00 sockets. NAT64, coverage, commissioning UNVERIFIED until a device exists.
Report: services/matter/TADO-X-READINESS.md.

## 2026-10-30 — HA migration Phase 3
Moved to homelab-notebook (NixOS). Vendor-ID gotcha: must pass `--vendorid=65521`; the module default 4939 crashed it with a FabricAdmin collision and rewrote chip.json (re-copied). Loaded 0 nodes, HA connected. casaos container removed; `/footage/services/matter/data.bak-pre-move-20261030` kept.

## 2026-10-30 — Container name fix; migration Phase 0
The container is `matter-server`, not `matter` (`docker inspect matter` fails); README corrected.
Version 8.1.2, same as nixpkgs. Data dir holds the fabric JSON + chip*.ini + credentials/ (1.3M).
Migration plan: `../homeassistant/MIGRATION.md` (Phase 3). No change to the running service.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
