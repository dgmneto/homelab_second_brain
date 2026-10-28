# Logbook — tailscale

Reverse-chronological. Newest entry on top. One entry per task that touches **tailscale** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-28 — Installed on casaos as tagged subnet router
Native apt install (1.104.4) from pkgs.tailscale.com bookworm repo; persisted `net.ipv4.ip_forward=1`
(IPv6 forwarding left off on purpose — would kill SLAAC). Joined with one-off key
`op://Personal/Tailscale/CasaOs Auth Key` staged in `/dev/shm` and shredded by trap; flags
`--hostname=casaos --advertise-tags=tag:server --advertise-routes=192.168.11.0/24,192.168.14.0/24,192.168.15.0/24
--ssh --accept-dns=false --accept-routes=false --operator=dgmneto`. User added tagOwners/autoApprovers/ssh
rules to the tailnet policy. Verified: node `100.79.139.39` online, `tag:server`, KeyExpiry null;
`.11` + `.14` routes primary (auto-approved); `.15` advertised but pending manual approval (not in
autoApprovers); resolv.conf unchanged (192.168.11.1); 23/23 containers up, same set as pre-install
snapshot; host IPv6 RA routes intact; overseerr.intern still 307 from LAN. Not yet verified: end-to-end
from an off-LAN tailnet device.
