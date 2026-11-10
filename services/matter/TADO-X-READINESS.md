# tado° X (Matter-over-Thread) — network readiness audit

**Date:** 2026-11-06 (read-only audit, cloud agent via Tailscale SSH as `claude`). **Scope:** network + Matter/Thread
infrastructure only — says nothing about heating wiring, boiler or valve compatibility.
Nothing was changed, restarted, installed or commissioned. No Thread credentials (PSKc, network key, active dataset,
XPAN ID) were read or recorded; the mDNS dump redacts `xp/at/pt/id`.

**Update 2026-11-10:** 6 tado° X devices are now commissioned and online in HA — see the device table in
[README.md](README.md#commissioned-devices-server-truth-2026-11-10). Firewall Stage 1 still not deployed.

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
   flap "unavailable" in HA. Not provable until a device exists (drops are silent — no LOG rule). Fix = staged log-then-accept rule scoped to
   `enp2s0` + `fde9:b6c5:757::/64` + unprivileged ports, plus a drift check (below).
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
1. **(Recommended, homelab-notebook — final version after two review rounds, 2026-11-06.)** Supersedes an earlier
   `fc00::/7` rule (too broad) and a `--dport 32768:60999` rule (tied to an OS setting). Staged, in
   `hosts/homelab-notebook/nixos/home-automation.nix` (matter block); deploy per host README. Nothing deployed yet.

   **Box facts behind it (verified 2026-11-06):**
   - Refused packets are **not logged** (`nixos-fw-log-refuse` → DROP, no LOG rule), so drops are silent today.
   - `/proc/net/nf_conntrack` is readable with sudo; there is no `conntrack` binary.
   - matter-server 8.1.2 **cannot pin** its Matter UDP port: `--port` is the TCP websocket only. The CHIP operational
     port is OS-assigned at every start (`[::]:47870` now; 39400/41266/49487/39939/59843 are its other UDP sockets).
   - matter-server runs as `DynamicUser` with an **empty `CapabilityBoundingSet`**, and `ip_unprivileged_port_start`
     is 1024, so it cannot bind a port below 1024 explicitly. Ports below 1024 on the box are system services (NTP
     123, DNS 53, DHCPv6 546), which the rule keeps excluded.
   - `ip_local_port_range` is 32768–60999 today. That is an OS setting, not a Matter guarantee, so the rule must not
     depend on it.
   - rpfilter (`nixos-fw-rpfilter`) is on, so a `fde9:b6c5:757::/64` source is only accepted on `enp2s0`, where its
     route points at the Apple TV.
   - **Identify sockets with `sudo ss -uapn`**, matching the unit's cgroup PIDs, **not** `systemctl … MainPID`. MainPID
     (32032) is the `matter-server-start` wrapper; the socket-owning python process is its child (32043). Without
     sudo, `ss` omits other users' process info.

   **Stage 0 (before install):** nothing.

   **Stage 1 (first days with devices) — log only, no accept:**
   ```nix
   networking.firewall.extraCommands = ''
     ip6tables -I nixos-fw-log-refuse -i enp2s0 -s fde9:b6c5:757::/64 -p udp \
       -m limit --limit 6/min -j LOG --log-prefix "thread-udp-refused: "
   '';
   networking.firewall.extraStopCommands = ''
     ip6tables -D nixos-fw-log-refuse -i enp2s0 -s fde9:b6c5:757::/64 -p udp \
       -m limit --limit 6/min -j LOG --log-prefix "thread-udp-refused: " 2>/dev/null || true
   '';
   ```
   The LOG target already records `SRC= DST= SPT= DPT=` with a kernel timestamp. Alongside it, run a passive
   conntrack snapshot for the observation window:
   ```
   sudo systemd-run --unit=ct-matter-watch -p RuntimeMaxSec=3d /bin/sh -c \
     'while :; do date -Is; grep fde9 /proc/net/nf_conntrack; sleep 30; done >> /var/tmp/ct-matter.log'
   ```
   **Count a refused packet as a conntrack-expiry drop only if all of these hold:**
   1. **DPT** is one of matter-server's UDP ports per `sudo ss -uapn` (cgroup PIDs:
      `cat /sys/fs/cgroup$(systemctl show -p ControlGroup --value matter-server)/cgroup.procs`), **and**
      `systemctl show matter-server -p ActiveEnterTimestamp` predates the drop. A restart changes the port; a drop
      to an old port is a stale device session, not conntrack.
   2. **DST** is an address `enp2s0` still holds (`ip -6 addr show dev enp2s0`, including temporaries). A drop to a
      removed privacy address means address churn, not conntrack.
   3. **Timing:** the drop's (SRC,SPT,DST,DPT) equals the reply-direction tuple of an entry in `ct-matter.log`. That
      entry's timeout counted down and the entry vanished before the drop's timestamp, i.e. the gap since its last
      refresh was ≥ `nf_conntrack_udp_timeout_stream` (120 s).
   4. A matching symptom in the same minute: the device goes unavailable in HA, or `journalctl -u matter-server`
      shows a resubscribe/timeout for that node.

   **Stage 2 (only if Stage 1 shows drops meeting 1–4):** replace the LOG rule with an accept rule bound to the
   interface and the advertised Thread prefix, excluding privileged ports. It does **not** depend on
   `ip_local_port_range`. Add the matching `-D` in `extraStopCommands`:
   ```
   ip6tables -A nixos-fw -i enp2s0 -s fde9:b6c5:757::/64 -p udp --dport 1024:65535 -j nixos-fw-accept
   ```
   Extra exposure versus today: only unprivileged UDP sockets on the box (matter-server's, HA's ephemeral ones), and
   only to Thread nodes.

   **Drift detection (so the rule can't silently stop matching):** [`tools/matter-fw-check.sh`](tools/matter-fw-check.sh)
   exits 1 with a `WARN` line if any of these hold:
   - the advertised Thread prefix (RIO) ≠ the rule's prefix;
   - there is no Thread route (border router down);
   - a matter-server UDP socket (other than 5353) is below the rule's lower bound;
   - with `CHECK_RULE=1`, the accept rule isn't loaded.

   Verified 2026-11-06: exits 0 on the current state, and produces all three WARNs when given a wrong prefix, a high
   lower bound and `CHECK_RULE=1`. Suggested wiring at Stage 2: a oneshot unit running it hourly
   (`OnCalendar=hourly`) and 1 min after `matter-server` starts (the port is chosen then), with failures visible via
   `systemctl --failed` / journal. Not deployed.

   **Not chosen as primary:** raising `net.netfilter.nf_conntrack_udp_timeout_stream` to 3600. It applies to every
   replied UDP flow on the box (Pi-hole upstream DNS, Tailscale), and it doesn't help when there is no live entry
   (idle > 3600 s, matter-server restart → new port, conntrack flush). At most a complement.
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
