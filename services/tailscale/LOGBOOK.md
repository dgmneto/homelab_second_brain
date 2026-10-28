# Logbook — tailscale

Reverse-chronological. Newest entry on top. One entry per task that touches **tailscale** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-28 — SessionStart hook: cloud sessions auto-join the tailnet
Added `.claude/hooks/session-start.sh` + `.claude/settings.json` so every Claude cloud session joins the
tailnet (ephemeral `--state=mem:`, `TS_AUTHKEY`) and gets `ssh casaos`/`homelab`/`homelab-notebook`
config. Verified from scratch in this session: hook rc=0 in 11 s, node `claude-cloud-session`
100.89.53.35 `tag:claude`; re-run 0.03 s; no-op outside remote. `ssh casaos` still denied by tailnet SSH
policy for `tag:claude` (ACL change pending on the user's side).

## 2026-10-28 — Joined a Claude cloud session to the tailnet
Downloaded tailscale 1.104.4 static tgz into the session, ran tailscaled in userspace mode, `up` with the
env-provided `TS_AUTHKEY` → node `claude-cloud-session-1` (100.66.0.85, `tag:claude`). Verified:
`tailscale ping casaos` pongs via DERP(lhr); SSH banners read from `100.79.139.39:22` (Tailscale) and
`192.168.11.13:22` (OpenSSH via subnet route). Tailscale SSH as `dgmneto` **denied by tailnet policy**
for `tag:claude` — needs an ssh ACL rule (see README). Recipe + gotchas added to README.

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
