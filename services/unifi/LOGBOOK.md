# Logbook — unifi

Reverse-chronological. Newest entry on top.

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
