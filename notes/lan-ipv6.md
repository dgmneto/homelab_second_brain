---
name: lan-ipv6
description: LAN has native IPv6 from Zen since 2026-11-01 (delegated /48 2a02:8012:882b::/48; Default LAN = 2a02:8012:882b::/64 via SLAAC). The old ULA fd00::/64 is NO LONGER advertised (gone by 2026-11-06). Thread BR = Apple TV 192.168.11.236, OMR route fde9:b6c5:757::/64. Never disable IPv6 - Matter/Thread needs it; inbound IPv6 relies on the UniFi firewall.
metadata:
  node_type: memory
  type: reference
---
# LAN IPv6 (native since 2026-11-01)

> **Update 2026-11-06 (RA captured with `services/matter/tools/ra.py`):** UniFi's RA now carries **only**
> `2a02:8012:882b::/64` — the ULA `fd00::/64` below is **gone** (hosts have no `fd00::` address any more; some long-running
> processes still hold stale `fd00::` sockets/advertisements until restarted). The Thread border router
> `fe80::67:28bc:f5ae:b3b6` / `c4:f7:c1:12:02:5f` **is the Apple TV 4K (gen 3) `192.168.11.236`** ("Living Room");
> it sends router-lifetime-0 RAs with RIO `fde9:b6c5:757::/64`. Full Matter/Thread picture:
> [services/matter/TADO-X-READINESS.md](../services/matter/TADO-X-READINESS.md).

**State (verified 2026-11-01 17:23 from both servers):**
- ISP **Zen**: WAN link net `2a02:8011:d017:bb39::/64` ("IPv6 ND WAN"); **delegated prefix `2a02:8012:882b::/48`** ("IPv6 PD LAN",
  shown in My Zen). UniFi WAN: DHCPv6, prefix delegation size 48.
- UniFi network **Default** (`192.168.11.0/24`) = Prefix Delegation + SLAAC → RA now carries **`2a02:8012:882b::/64`**
  *and* the old ULA **`fd00::/64`**, router lifetime 1800 s, RDNSS `2a02:8012:882b::1`. Router: `192.168.11.1` /
  `fe80::7a45:58ff:feb1:a57d` (UniFi).
- casaos and homelab-notebook each have a `2a02:8012:882b:0:…` SLAAC address (+ temporary/privacy ones on the laptop);
  `curl -6 https://ipv6.google.com` → 200, ping6 Google DNS ~6 ms. casaos' VLAN 14/15 macvlan nets still ULA-only
  (`fd00:1::`/`fd00:2::`; not changed).
- Thread border router (`fe80::67:28bc:f5ae:b3b6`, MAC `c4:f7:c1…`) still advertises its mesh prefix `fde9:b6c5:757::/64`;
  route present after the change. **Never disable IPv6 on hosts/LAN**: Matter over Thread depends on it.

**Before 2026-11-01:** router advertised only `fd00::/64` plus a default route with no upstream, so IPv6 egress failed instantly
(happy eyeballs → IPv4); WAN IPv6 simply wasn't enabled in UniFi.

**Inbound exposure:** every host now has a globally routable address. Protection = UniFi's IPv6 firewall (default: block
unsolicited inbound from the internet) + per-host firewalls (homelab-notebook: NixOS firewall covers v6; **casaos has no host
firewall and Docker publishes ports on `[::]`**). **Config verified 2026-11-11** via the UniFi API: only predefined zone policies, External→Internal = block (IPv4 *and*
IPv6), no custom allow rules ([services/unifi](../services/unifi/README.md)). Not yet verified from outside (the cloud agent has no IPv6). To verify, from an
IPv6-capable network outside the LAN (e.g. phone on mobile data): connect to `[<host v6>]:22/8123/53` → must fail.

Check quickly: `ip -6 addr show scope global | grep 'inet6 2'` and `curl -6 -s -o /dev/null -w '%{http_code}' https://ipv6.google.com`.
RA dump: `sudo nix shell nixpkgs#ndisc6 -c rdisc6 -w 3000 -r 3 enp2s0` (on homelab-notebook).

## 2026-11-11 — UniFi RA now sourced from a GUA (broken)
`tools/ra.py` (services/matter/tools): the UniFi (`78:45:58:b1:a5:7d`) advertises `2a02:8012:882b::/64`, router lifetime 1800 s,
**from `2a02:8012:882b::1`**, not from its link-local `fe80::7a45:58ff:feb1:a57d` (that address no longer answers ND). Hosts must
ignore the router part, so homelab-notebook and casaos have **no IPv6 default route** (the on-link /64 is still installed).
Seen together with all tado/Thread devices becoming unreachable at 06:27. Fix is on the UniFi; see services/matter/README.md.
**Trigger found (UniFi system log, via `services/unifi/tools/unifi.sh`):** overnight auto-update — UDR firmware **5.1.35 → 6.0.17**
at 04:02:59 UTC, UniFi Network **10.6.109 → 11.0.99** at 04:17:23 UTC. No IPv6 config change: Default is still PD + SLAAC, RA on,
priority high, preferred lifetime 14400. Still broken at 12:45 (RA from `2a02:8012:882b::1`, valid 54884 s). No public bug report
found yet. Auto-update is on (daily 03:00, apps included). **Fixed by a UDR restart at 12:51 UTC**: RA from `fe80::7a45:58ff:feb1:a57d` again,
v6 default route + `curl -6 ipv6.google.com` 200 on homelab-notebook at 12:54.

