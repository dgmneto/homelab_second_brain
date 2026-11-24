# thread (Thread mesh + border routers)

The home's single Thread network, used by the 6 tado° X devices (Matter over Thread; see [../matter](../matter/README.md)).
Not a host service: it lives on the border routers below. HA/matter-server reach it over IPv6 on the Default LAN.

| | |
|---|---|
| Network name | `MyHome1662126353` (created by Apple Home) |
| Channel / PAN ID | **25** / `0x92ea` (same 2.4 GHz channel as the Zigbee network on the SLZB-06M, z2m `channel: 25`) |
| Mesh-local prefix | `fd78:ebf6:9d69:4da2::/64` |
| OMR prefix (LAN-routable) | `fde9:b6c5:757::/64`, published by the Apple TV (leader) |
| Credentials (dataset TLV) | HA `/var/lib/hass/.storage/thread.datasets`, source `iOS-app` (synced 2026-11-10 from the HA Companion app), = HA's preferred dataset. **Never print or commit it**; [`tools/push_dataset.py`](tools/push_dataset.py) pipes it straight to an OTBR. |

## Border routers (since 2026-11-24)

| BR | IP / link-local | Thread role | Notes |
|---|---|---|---|
| Apple TV 4K gen 3 "Living Room" | `192.168.11.236`, `fe80::189f:c96:5398:f346` (**changed**; was `fe80::67:28bc:f5ae:b3b6` on 11-06), MAC `c4:f7:c1:12:02:5f` | **leader**, router id 28 (rloc `0x7000`) | Parent of all 6 tado devices (all sleepy end devices). Never run Tailscale on it (see matter README). |
| **SMLIGHT SLZB-MR5U** | `192.168.11.121` (DHCP, MAC `90:DA:72:FA:B9:10`; Ethernet MAC `92:da:72:fa:b9:10`), `fe80::90da:72ff:fefa:b910` | router, id 56 (rloc `0xe000`), link quality 3/3 both ways to the Apple TV | **Radio 2** (EFR32MG24) in mode "Thread+OTBR running on device" (OTBR runs on the ESP32-S3, RCP fw `20251218`). **Radio 1 is still Zigbee coordinator fw 20250212, unused** (socket 6638). SLZB-OS v3.2.6.dev3 (dev channel). |

The SLZB-MR5U exposes the **OTBR REST API at `http://192.168.11.121:8080`** (no auth): `/node`, `/node/state`
(`GET`; `PUT "enable"|"disable"`), `/node/dataset/active` (`PUT` hex TLV as `text/plain`), `/diagnostics` (mesh-wide
network diagnostics: every router's route table, child table, MAC counters). `/node/ba-state`, `/node/neighbors` → 404.
Web UI `http://192.168.11.121/` (Mode page = radio modes). mDNS: `_slzb-06._tcp` and `_meshcop._udp` "SLZB-MR5U".

With two BRs, LAN hosts get the OMR route from both RAs. On homelab-notebook NetworkManager merges them into an **ECMP
route** (`fde9:b6c5:757::/64 proto ra metric 105 pref low`, nexthops MR5U + Apple TV), so ~half of HA→tado packets enter
the mesh via the MR5U and take one extra Thread hop to the Apple TV.

## Gotchas (learned 2026-11-24)
- **Enabling "Thread+OTBR running on device" makes the OTBR form its OWN network** (`OpenThread-ESP`, ext PAN
  `dead00beef00cafe`, mesh-local `fd00:db8:a0::/64`) within ~1 min: it went `detached` → **`leader`**. Immediately
  `PUT /node/state "disable"`, push the Apple dataset, then `"enable"`. It attaches as `child` after ~30 s and becomes
  `router` after ~2 min. Don't leave a second network on the air, and don't let HA's OTBR config flow pick the ESP one.
- The mode switch asks for a **native `confirm()`** ("Confirm flashing firmware Thread Border Router 20251218"). The
  Claude built-in browser auto-dismisses native dialogs (returns false), so nothing happens. Before clicking, run
  `window.confirm = () => true` in the page via `javascript_tool`. The toggle opens an "Enable" modal first.
- The device needs internet for the mode switch (it downloads the RCP firmware).
- The dataset survives a reboot. After a UI reboot it was back as `router` 0xe000 in ~10 s. During that window, pings
  from homelab-notebook to a tado device lost ~10/150 because the ECMP route still points half the traffic at the dead
  BR (RIO lifetime 1800 s; Linux doesn't drop dead nexthops by default). Short reboots are harmless (matter-server
  retries). A **long** MR5U outage would halve LAN→Thread delivery until the RIO expires, so unplug it only briefly or
  disable its Thread first (`PUT /node/state "disable"`).
- Sleepy devices keep their parent until they re-attach, so a new router doesn't change their path right away. All 6
  were still children of the Apple TV right after the join.
- Ping RTTs to the tado devices are **~0.03–3 s (avg ~1.5 s)**. That's their sleepy-end-device poll interval, not link
  quality. Compare **loss** and the Apple TV's MAC counters, not RTT.
- **HA `otbr` integration added 2026-11-24** (URL `http://192.168.11.121:8080`; shortcut:
  `http://192.168.11.21:8123/config/integrations/dashboard/add?domain=otbr`). It kept the OTBR's existing (Apple) dataset:
  partition/rloc unchanged. HA → Settings → Thread now shows preferred network `MyHome1662126353` with **2 border routers**
  (Living Room, SLZB-MR5U). This is visibility/management only. Matter traffic doesn't depend on it. The MR5U is
  also offered as a discovered **SMLIGHT** integration; not added (would only add device sensors).
- The Claude built-in browser pane keeps its own HA session: the user must sign in **in the pane**, not in their Chrome.

## Measuring quality (before/after method)
1. Node addresses: from the Mac, `dscacheutil -q host -a name <thread-hostname>.local` (hostnames in
   [`tools/nodes.txt`](tools/nodes.txt); re-derive with `dns-sd -L BFABFD88F60E01A6-<node hex> _matter._tcp`).
2. [`tools/mac_ping.sh <label>`](tools/mac_ping.sh) (Mac, Wi-Fi, 30 pings/node) and, wired from homelab-notebook,
   `ssh homelab-notebook "bash -s <label> 2=Name=addr …" < tools/nb_ping.sh` (60 pings/node, plus 7-day matter-server
   counts of `Marked node as unavailable` / `Subscription Liveness timeout` / `CASESession timed out` / resubscribe).
3. Mesh view: `curl -s http://192.168.11.121:8080/diagnostics` (strip `NetworkData` before saving).

Raw results: [measurements/2026-11-24/](measurements/2026-11-24/). Summary:

| Metric (wired, 60 pings/node) | Before (15:58Z, Apple TV only) | After (16:10Z, + MR5U) |
|---|---|---|
| Loss Living Room thermostat / Hall thermostat / Guest TRV | 0 / 0 / 0 % | 0 / 0 / 0 % |
| Loss Small Room TRV / Loft TRV | 1.7 / 1.7 % | 3.3 / 1.7 % |
| Loss Office TRV | **13.3 %** (avg 2.3 s, max 5.6 s) | 1.7 % (avg 1.4 s) |
| Avg RTT (all) | 1.35–2.31 s | 1.29–1.58 s |
| Mac (Wi-Fi, 30 pings) | 0 % loss all 6 | 0 % except Guest 3.3 % |
| Thread routers | 1 (Apple TV; star topology) | 2 (Apple TV + MR5U, LQ 3/3) |
| Border routers / LAN routes | 1 | 2 (ECMP) |
| matter-server 7-day | 35 unavailable, 263 liveness timeouts, 2200 CASE timeouts, 533 resubscribes | re-measure ≥ 2026-12-01 |

Read: the IP-level difference right after the join is within noise. The Office TRV improvement can't be pinned on
the MR5U, because every device was still parented by the Apple TV. Real gains come from the **redundancy** (2nd BR, 2nd
router) and from devices re-attaching to the MR5U if it is closer to them. Apple TV MAC counters at 16:09Z:
11054 unicast in, **572 in-discards**, 12 in-errors, 20 out-errors/discards. Re-run `/diagnostics` later and compare
them and the child tables.

**Follow-ups:** re-measure after ~1 week (2026-12-01): the 7-day log counts, which children moved to the MR5U.
Consider moving Thread or Zigbee off **channel 25**: both meshes share it today. That's a Zigbee/Apple change, not
done here.
