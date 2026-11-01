---
name: lan-ipv6
description: The home LAN has no public IPv6 (router hands out ULA fd00::/64 only but still advertises a default route); IPv6 internet connections fail instantly and fall back to IPv4. Keep ULA - Matter/Thread needs it.
metadata:
  type: fact
---
# LAN IPv6: ULA only, no internet IPv6 (verified 2026-11-01)

- Every host (casaos, homelab-notebook) has only `fd00::/64` (+ casaos' macvlan `fd00:1::`/`fd00:2::`) and the
  Tailscale `fd7a:…` address. **No global (2xxx:) address anywhere.**
- The router (`192.168.11.1`, MAC `78:45:58:b1:a5:7d` → Ubiquiti/UniFi OUI) sends RAs for `fd00::/64` **and** a default
  route (`default via fe80::7a45:58ff:feb1:a57d … pref high`), but has no IPv6 upstream. So `curl -6` to anything on the
  internet fails immediately (code 000), and apps fall back to IPv4 (happy eyeballs). Observed impact: none.
- `fde9:b6c5:757::/64` via `fe80::67:28bc:f5ae:b3b6` (MAC `c4:f7:c1…`) is the **Thread border router's** mesh prefix. Matter
  over Thread depends on it and on the ULA addresses, so **never "fix" IPv6 by disabling it** on hosts or the LAN.
- Real fix is on the router/ISP (user action): if the ISP offers IPv6, enable it on the WAN (DHCPv6 with prefix delegation,
  typically /56 or /60) and set the LAN network's IPv6 to prefix delegation + SLAAC; hosts then get global addresses
  automatically and keep the ULA. If the ISP has no IPv6, the only tidy-up is stopping the router advertising itself as an IPv6
  default gateway; purely cosmetic.
- Check quickly: `ip -6 addr show scope global` (look for a non-fd address) and `curl -6 -s -o /dev/null -w '%{http_code}' https://ipv6.google.com`.
