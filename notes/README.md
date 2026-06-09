# notes/ — project memory

Durable, cross-cutting homelab knowledge that isn't tied to one service/cron/access doc. This is the
in-repo home for what used to live in the agent's `~/.claude` memory store — version-controlled so
every agent sees the same facts and can correct them (see the self-improvement mandate in
`../CLAUDE.md`).

Index:
- [ssh-access](ssh-access.md) — SSH into the server; bypass the broken 1Password agent.
- [footage-disk-leak](footage-disk-leak.md) — recurring `/footage` 100%-full outage (chrome.service
  leak) that surfaces as Home Assistant "down".
- [qbittorrent-mass-stop](qbittorrent-mass-stop.md) — "all downloads paused" is usually a watchtower
  restart, not VPN/disk; how to diagnose via the Chrome WebUI.

When you learn a new durable fact (or correct one of these), update the file and this index, then
commit + push.
