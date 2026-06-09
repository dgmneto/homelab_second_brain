# notes/ — project memory (symlinked to the harness memory store)

Durable, cross-cutting homelab knowledge that isn't tied to one service/cron/access doc. This folder
**is** the agent's auto-memory: the harness memory directory is symlinked here, so what auto-recall
loads at session start and what gets committed to git are the same files.

Each `*.md` is one memory with frontmatter (`name`, `description`, `metadata.type`); `MEMORY.md` is the
index that recall reads (one line per memory). Link related memories inline with `[[name]]`.

## The symlink (Mac-local, not in git — recreate per machine)
```
ln -s /Users/dgmneto/homelab/notes \
  /Users/dgmneto/.claude/projects/-Users-dgmneto-homelab/memory
```
The harness path is fixed and per-machine; cloning this repo does not recreate the link. On a fresh
machine, point that project's `memory` dir at this folder. New memories the harness writes land here as
new `*.md` + a `MEMORY.md` line — commit and push them like any other change.

## Memories
- [ssh-access](ssh-access.md) — SSH in; bypass the broken 1Password agent.
- [footage-disk-leak](footage-disk-leak.md) — recurring `/footage` 100%-full outage (chrome.service
  leak) that surfaces as Home Assistant "down".
- [qbittorrent-mass-stop](qbittorrent-mass-stop.md) — "all downloads paused" is usually a watchtower
  restart, not VPN/disk; diagnose via the Chrome WebUI.
