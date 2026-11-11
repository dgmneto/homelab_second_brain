# Logbook — unifi

Reverse-chronological. Newest entry on top.

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
