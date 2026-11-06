# tado° X (Matter-over-Thread) — network readiness audit

**Date:** 2026-11-06 (read-only audit, cloud agent via Tailscale SSH as `claude`). **Scope:** network + Matter/Thread
infrastructure only — says nothing about heating wiring, boiler or valve compatibility.
Nothing was changed, restarted, installed or commissioned. No Thread credentials (PSKc, network key, active dataset,
XPAN ID) were read or recorded; the mDNS dump redacts `xp/at/pt/id`.

Re-run the evidence any time with the two scripts in [tools/](tools/) (see "How to re-check" at the bottom).

## Inventory as found (vs. what the task brief assumed)

| Brief said | Server truth (2026-11-06) |
|---|---|
| HA + Matter Server in Docker | **Native NixOS services on `homelab-notebook` `192.168.11.21`** (`home-assistant.service` 2026.10.4, `matter-server.service` python-matter-server **8.1.2**), no Docker. casaos has **no** HA/matter/z2m/mosquitto containers left. |
| Docker bridge/macvlan may matter | Irrelevant to Matter now: matter-server runs in the host network namespace on `enp2s0`. (casaos' `macVlanIPv6Network` / VLAN 14/15 no longer carry any Matter traffic.) |
| Apple TV 4K, model unknown | `Living Room`, **`AppleTV14,1` = Apple TV 4K (3rd gen)**, tvOS 27.2, `192.168.11.236`, MAC `c4:f7:c1:12:02:5f`, same L2 as HA. It **is** an active Thread border router → must be the **A2843 (Wi-Fi + Ethernet, 128 GB)**; the 64 GB Wi-Fi-only A2737 has no Thread radio. |
| SLZB-06M Zigbee coordinator | `192.168.11.228:6638`, Zigbee (ember) for zigbee2mqtt — **not** a Thread radio. |
| Multiple VLANs | Apple TV, homelab-notebook, SLZB, router all on **Default `192.168.11.0/24`** (one L2: link-local ping 1.2 ms, mDNS seen directly). VLAN 14/15 exist on casaos only. |

## Evidence

**Thread border router (passive mDNS from `enp2s0`, `tools/browse.py`):**
- Exactly **one** `_meshcop._udp` border agent on the LAN: `Living Room` @ `Living-Room.local` →
  `192.168.11.236`, `2a02:8012:882b:0:1c38:bf3c:dd2c:4c4a`, `fe80::67:28bc:f5ae:b3b6`; `vn=Apple`,
  `mn=BorderRouter`, Thread version `tv=1.4.0`, network name `MyHome1662126353`, domain `DefaultDomain`.
- State bitmap `sb=0x00000fb1` → interface **active/attached**, high availability, **Backbone Router active +
  primary**, Thread role **leader**, ePSKc supported.
- Also advertises `_trel._udp` (Thread over infrastructure link) and `_srpl-tls._tcp` (SRP server, domain
  `openthread.thread.home.arpa.`) — i.e. the full Apple BR service set.
- Same host's `_airplay._tcp` record: `model=AppleTV14,1`, `osvers=27.2`. HA's `apple_tv` integration device
  registry: "Apple TV 4K (gen 3)".
- No other Thread BR (no HomePod, Nest, OTBR, SkyConnect) seen. The Apple TV is the **only** BR.

**IPv6 / RA (`tools/ra.py`: one Router Solicitation, 12 s listen):**
- UniFi `fe80::7a45:58ff:feb1:a57d`: default router (lifetime 1800 s), PIO `2a02:8012:882b::/64` (A=1, L=1), RDNSS
  `2a02:8012:882b::1`, MTU 1500. **The ULA `fd00::/64` is no longer advertised** (was on 2026-11-01).
- Apple TV `fe80::67:28bc:f5ae:b3b6`: router lifetime **0** (not a default router — correct), **RIO
  `fde9:b6c5:757::/64` lifetime 1800 s** = the Thread off-mesh-routable (OMR) prefix. No PIO from it (it only adds its
  own on-link prefix when the LAN lacks one — the GUA prefix satisfies that).
- No PREF64 option from either router (expected: NAT64 is published inside Thread network data, not on Ethernet).
- `homelab-notebook` `enp2s0`: SLAAC GUAs in `2a02:8012:882b::/64` (+ privacy temps), link-local
  `fe80::ace7:3469:c9c6:1729`; route **`fde9:b6c5:757::/64 via fe80::67:28bc:f5ae:b3b6 dev enp2s0 proto ra`**
  installed (NetworkManager handles RA/RIO in userspace — kernel `accept_ra=0` on enp2s0 is normal here).
  Default v6 route via UniFi. `ping -6 fe80::67:28bc:f5ae:b3b6%enp2s0` 0 % loss, 1.2 ms. Joined `ff02::fb`.

**Matter Server:** `matter-server.service` active since 2026-10-30 22:23, 0 restarts, args
`--primary-interface=enp2s0 --vendorid=65521 --port=5580`; log: "Using 'enp2s0' as primary interface", fabric
`0x1` VendorId 0xFFF1, **0 nodes**; no errors since. Its own operational record
`…-000000000001B669._matter._tcp` is visible on the LAN with GUA + link-local. Listens: TCP `5580` (ws), UDP
`[::]:47870` (CHIP operational, **ephemeral — changes each start**), 5353.
**HA:** `matter` entry → `ws://192.168.11.21:5580/ws` (loaded); `thread` entry exists (zeroconf); **no
`.storage/thread.datasets`** → HA has no Thread dataset/credentials and no preferred network. No
`components.matter|thread` warnings/errors in the journal since HA start (2026-11-01 15:16).
**Firewall (NixOS iptables, default drop):** inbound UDP 5353, TCP 5580, all ICMPv6 except redirect (137/139)
accepted; conntrack RELATED/ESTABLISHED accepted; `nf_conntrack_udp_timeout(_stream)` = 30/120 s.
**UniFi:** controller not queried (no API credential for the agent; the HA `unifiprotect` login was deliberately not
reused). VLAN/firewall facts are inferred from the L2 observations above.

## Readiness matrix

| Component | Status | Evidence | Recommended action |
|---|---|---|---|
| Apple TV Thread eligibility | **PASS** | `AppleTV14,1` (gen 3) and it is actively running a Thread BR (meshcop/TREL/SRP) — only the 128 GB Wi-Fi+Ethernet A2843 can. | Optional confirm: Apple TV → Settings → General → About shows model **A2843**. |
| Apple TV Thread border router | **PASS** | Sole `_meshcop._udp` agent, `sb` = active, leader, BBR primary; RIO `fde9:b6c5:757::/64` on the LAN. | Keep it on Ethernet + always powered; don't put it on a smart plug. |
| Thread/NAT64 support | **UNVERIFIED** | Apple BRs implement NAT64, but it is only visible in Thread network data (needs a Thread device/diag tool). tado requires NAT64 for the tado app via a third-party BR. | After adding the first tado X device: it must appear **online in the tado app** (cloud path = NAT64). If it shows only in Apple Home → NAT64 problem. |
| Home Assistant Matter integration | **PASS** (0 devices) | `matter` config entry → `ws://192.168.11.21:5580/ws`, loaded, no errors. | None. |
| Matter Server health | **PASS** | 8.1.2 up 7 days, 0 restarts, no errors, primary iface `enp2s0`, advertising `_matter._tcp`. | Minor: it still holds an mDNS socket on a stale ULA `fd00::3ec2:…` — restart matter-server (+HA) once in a maintenance window. |
| Docker IPv6 connectivity | **N/A → PASS** | No Docker in the Matter path; matter-server is in the host netns with GUA + link-local on `enp2s0`. | None. Do **not** move it back into Docker/macvlan. |
| Local IPv6 routing | **PASS** (route) / **UNVERIFIED** (end-to-end) | `fde9:b6c5:757::/64 via fe80::67:28bc:f5ae:b3b6 dev enp2s0`; BR reachable 1.2 ms. No Thread node exists yet to ping. | After install: `ping -6` a tado device's `fde9:b6c5:757:…` address from homelab-notebook. |
| mDNS/DNS-SD discovery | **PASS** | From matter-server's interface: Apple meshcop/TREL/SRP + own `_matter._tcp` visible; UDP 5353 open. `_matterc._udp`/`_matter._tcp` of Thread devices untestable until one exists. | None now. |
| UniFi VLAN/firewall configuration | **PASS** (inferred, same L2) / **UNVERIFIED** (controller) | BR, HA, router all on Default `192.168.11.0/24`; link-local + multicast work between them. No inter-VLAN hop in the Matter path. | In UniFi: keep the Apple TV and homelab-notebook on **Default**; don't enable *Client Device Isolation* / *Block LAN↔WLAN multicast* on the iPhone's SSID; keep IPv6 SLAAC/RA on Default. |
| Apple Home / HA coexistence | **READY (network)** / **UNVERIFIED** (commissioning) | HA has no Thread dataset — fine for multi-admin (HA joins Apple's fabric over IP via the BR; no credentials needed). | Commission in Apple Home/tado app first, then share to HA (pairing code). Credential sync only if you ever commission Thread devices *directly* from HA. |
| Thread radio coverage | **UNVERIFIED** | One BR, one location; IP tests cannot measure 802.15.4 coverage across three floors. | Post-install coverage test (below); add a 2nd Apple BR (HomePod mini) or tado Wireless Receiver X if a floor is weak. |

## Classified issues

**Verified failures:** none.

**Suspected issues (fix cheaply before install):**
1. **NixOS firewall vs. Matter operational UDP.** The CHIP controller uses an ephemeral UDP port (`47870` now), not
   opened in `nixos-fw`. Device→controller traffic that arrives after the 120 s UDP conntrack entry expired (subscription
   reports from sleepy battery TRVs with long max-intervals, ICD check-ins) would be dropped as NEW and the device would
   flap "unavailable" in HA. Not provable until a device exists. Fix = accept UDP from the Thread ULA range (below).
2. **Stale ULA in long-running processes.** UniFi stopped advertising `fd00::/64`; matter-server still has a socket on
   `fd00::3ec2:4890:5ead:c7c3`, and HA's HomeKit bridge advertises only `fd00::` v6 addresses. Wildcard sockets keep
   things working; a restart in a maintenance window cleans it up.
3. **Single border router.** The Apple TV is the only BR; if it is unplugged/rebooting, all Thread devices lose IP
   reachability from HA and the tado cloud.
4. (Side hint, not Matter-critical) the Plex investigation saw a hard ~94 Mbps ceiling to this Apple TV — looks like a
   100 Mbps Ethernet link (cable/switch port). Worth a cable check; it does not affect Thread.

**Cannot be confirmed until a tado device is installed:** NAT64/cloud path (tado app online), SRP registration of the
device, `_matterc._udp` / `_matter._tcp` discovery of a Thread node from HA, end-to-end IPv6 to `fde9:b6c5:757::/64`,
multi-admin share to HA, radio coverage on each floor.

## Post-installation coverage test (practical)
1. Add devices in the tado app (Thread network = Apple's). Each must be **online in the tado app** and present in Apple
   Home.
2. Per room: change a setpoint in the tado app and in Apple Home; it should react in < ~5 s. Repeat at the farthest
   floor. A device that is slow or drops is a coverage problem, not an IP one.
3. In HA (after sharing): Settings → Devices → the tado device → Matter info shows network type Thread and its
   IPv6 addresses; HA Thread panel lists `MyHome1662126353` / Apple BR. From the laptop:
   `ping -6 -c5 <device fde9:b6c5:757:… address>` — loss on far-floor devices = weak mesh.
4. Leave it 48 h; check `journalctl -u matter-server | grep -iE "unavailable|resubscri|timeout"`. Repeated resubscribe
   on one device = coverage; on all devices after ~2 min idle = the firewall/conntrack issue above.
5. Weak floor → add a mains-powered Thread router there (HomePod mini = 2nd Apple BR, or tado Wireless Receiver X).
   Battery TRVs do not extend the mesh.

## Prioritised changes before installation
1. **(Recommended, homelab-notebook)** in `hosts/homelab-notebook/nixos/home-automation.nix`, matter block, allow
   Matter traffic from Thread ULAs, then deploy per the host README:
   ```nix
   networking.firewall.extraCommands = ''
     ip6tables -A nixos-fw -p udp -s fc00::/7 -j nixos-fw-accept
   '';
   ```
   (`fc00::/7` survives Apple regenerating the mesh prefix; the current one is `fde9:b6c5:757::/64`.)
2. **(Low)** restart `matter-server` then `home-assistant` once (drops the stale `fd00::` bindings) — any quiet time
   before commissioning.
3. **(UniFi, verify only)** Apple TV `192.168.11.236` and homelab-notebook `192.168.11.21` stay on network **Default**;
   iPhone's SSID: Client Device Isolation off, LAN↔WLAN multicast not blocked; IPv6 on Default stays SLAAC with
   prefix delegation. Optionally add a DHCP reservation for the Apple TV.
4. **(Optional)** confirm A2843 on the Apple TV's About screen; make sure it's signed into the same Home as the iPhone
   and is the Home Hub (Home app → Home Settings → Home Hubs & Bridges → "Connected").
5. **(Do not)** sync Thread credentials into HA, add an OTBR/SkyConnect, or reflash the SLZB-06M to Thread — none
   needed for this design and a second, separate Thread network would fragment the mesh.

## How to re-check
From a Claude cloud session (`ssh claude@homelab-notebook`), using HA's own python + zeroconf (nothing installed):
```
PY=/nix/store/xahxrjs30p3mw0a42bqg9ikgkikskw8m-python3-3.14.8/bin/python3.14   # = readlink /proc/$(systemctl show -p MainPID --value home-assistant)/exe
ssh claude@homelab-notebook "$PY -I - <zeroconf site-packages> <ifaddr site-packages>" < services/matter/tools/browse.py
ssh claude@homelab-notebook "sudo $PY -I -" < services/matter/tools/ra.py
```
Site-package paths: `grep -o '/nix/store/[^ ,]*\(zeroconf\|ifaddr\)[^ ,]*site-packages'` in
`$(dirname …homeassistant…)/bin/.hass-wrapped`. Store paths change on every HA update — re-derive, don't trust these.
`browse.py` binds the interface addresses hard-coded at its top — update them if the laptop's IP changes.
