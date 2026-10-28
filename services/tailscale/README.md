# tailscale

Remote access to the whole homelab LAN. Runs on **casaos**, **natively** (apt package + systemd
`tailscaled`), **not** in Docker — on purpose: it's the remote lifeline, so it must survive Docker /
gluetun breakage, and it stays out of watchtower's weekly `:latest` pulls.

Installed 2026-10-28, version 1.104.4 from `https://pkgs.tailscale.com/stable/debian` (bookworm).
Updates come via `apt` (not watchtower).

## Node

| | |
|---|---|
| Tailnet name | `casaos` → `casaos.tailaec82a.ts.net` |
| Tailscale IP | `100.79.139.39` |
| Tag | `tag:server` (tagged ⇒ node key expiry disabled automatically) |
| Subnet routes advertised | `192.168.11.0/24` (LAN), `192.168.14.0/24` (VLAN 14 macvlan: NPM, Plex), `192.168.15.0/24` (VLAN 15 macvlan) |
| Tailscale SSH | on — `ssh dgmneto@casaos` from any tailnet device, no 1Password agent needed |
| Operator | `dgmneto` — `tailscale set …` works without sudo |

`up` flags used (re-run with the same set if you ever `tailscale up` again — `up` resets omitted flags):
```
--hostname=casaos --advertise-tags=tag:server \
--advertise-routes=192.168.11.0/24,192.168.14.0/24,192.168.15.0/24 \
--ssh --accept-dns=false --accept-routes=false --operator=dgmneto
```
Prefer `tailscale set --<flag>` for single changes; it doesn't reset the others.

## Why these flags (don't "fix" them)
- **`--accept-dns=false`** — otherwise Tailscale rewrites `/etc/resolv.conf`, and every container that
  inherits host DNS would start resolving through MagicDNS. Host stays on `nameserver 192.168.11.1`.
- **`--accept-routes=false`** — the box is *on* these subnets; accepting tailnet routes risks hijacking its own LAN.
- **IPv6 forwarding deliberately OFF.** Only `net.ipv4.ip_forward = 1` is persisted
  (`/etc/sysctl.d/99-tailscale.conf`). Turning on `net.ipv6.conf.all.forwarding` makes Linux ignore
  router advertisements, so the host would lose its SLAAC IPv6 addresses/routes. `tailscale up` prints
  "Warning: IPv6 forwarding is disabled" — expected, harmless (only IPv4 routes are advertised).
- Subnet routes are **SNATed** (default), so VLAN 14/15 hosts see traffic from `192.168.11.13` and
  reply via the router — no static routes for `100.64.0.0/10` needed anywhere.

## Tailnet policy (admin console → Access controls)
Required pieces (added 2026-10-28):
- `tagOwners`: `tag:server` → `autogroup:admin`
- `autoApprovers.routes`: `192.168.11.0/24`, `192.168.14.0/24` → `tag:server`.
  **`192.168.15.0/24` was NOT in autoApprovers at install** → needed a manual approve on the casaos
  device page (or add it to autoApprovers). Check with `tailscale status --json | jq .Self.PrimaryRoutes`.
- `ssh`: `{action: accept, src: [autogroup:admin], dst: [tag:server], users: [dgmneto]}` — the default
  SSH rule (`autogroup:self`) does **not** cover tagged devices.
- `ssh` (added 2026-10-28): `{action: accept, src: [tag:claude], dst: [tag:server], users: [claude]}` —
  lets Claude cloud sessions `ssh casaos` as the passwordless-sudo `claude` user (verified). Briefly was
  `users: [dgmneto]`; switched so agent actions are attributable and dgmneto keeps its sudo password.

## Claude cloud sessions (claude.ai/code) on the tailnet
**Automated:** [`.claude/hooks/session-start.sh`](../../.claude/hooks/session-start.sh) (SessionStart hook,
registered in `.claude/settings.json`, remote sessions only) does all of this at every session start:
downloads tailscale to `/opt/tailscale`, installs `openssh-client`, writes `~/.ssh/config` (`casaos`/
`homelab`/`homelab-notebook` via `tailscale nc` ProxyCommand), starts userspace `tailscaled` with
`--state=mem:` (node should register **ephemeral** per Tailscale docs, so no stale devices — not yet
confirmed in the admin console) and `tailscale up` with the env-injected **`TS_AUTHKEY`** (`tag:claude`).
Cold run ~11 s, warm re-run ~0.03 s. Default socket path → plain `tailscale status` works. If it
didn't run: `CLAUDE_CODE_REMOTE=true .claude/hooks/session-start.sh`; daemon log `/var/log/tailscaled.log`.

Manual equivalent (what the hook does):
```
curl -fsSL https://pkgs.tailscale.com/stable/tailscale_latest_amd64.tgz | tar xz -C /opt/tailscale --strip-components=1
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 --state=mem: &
tailscale up --auth-key="$TS_AUTHKEY" --hostname=claude-cloud-session --accept-routes
```
Gotchas (verified 2026-10-28):
- **`--socket` must be a short path** (the hook uses the default): the scratchpad path exceeds the unix-socket
  length limit → `bind: invalid argument` and tailscaled exits.
- Control plane + DERP work through the session's HTTPS proxy (tailscaled honours `HTTPS_PROXY`);
  traffic is DERP-relayed (`lhr`, ~115 ms), no direct path. Userspace mode → use
  `tailscale nc <host> <port>` as ssh `ProxyCommand` (or SOCKS5 on `localhost:1055`).
- No `ssh` client in the image by default (the hook installs `openssh-client`).
- `ssh casaos` (= Tailscale SSH as `claude`, no key needed, `sudo -n` works) **works** since the `tag:claude` ssh rule
  was added (see Tailnet policy above). If it ever says "tailnet policy does not permit you to SSH to this
  node", that rule is missing — it must sit **inside** the existing `"ssh": [ ... ]` array (pasting it at
  the policy's top level fails with `json: unknown field "action"`). `192.168.11.13:22` (OpenSSH via the
  subnet route) is also reachable but needs a key the session doesn't have. `dgmneto@` is refused (not
  in the rule's `users`).
- With file state, each session registered a new node (`claude-cloud-session-N`) that lingered offline;
  the hook's `--state=mem:` is meant to fix that. Delete pre-hook leftovers in the admin console.

## `*.intern.dgmneto.com` from outside
No split DNS needed: the names are in **public** DNS (Cloudflare) as CNAME → `intern.dgmneto.com` →
`192.168.14.34` (nginxIntern's macvlan IP). Off-LAN, they already resolve; Tailscale's `192.168.14.0/24`
route makes them reachable. If a name fails on some network, suspect that resolver's DNS-rebinding
protection (drops public answers with private IPs) — fix would be split DNS for `intern.dgmneto.com`
→ `192.168.11.1` in the admin console.

## Auth key
One-off, pre-approved, `tag:server` key at **`op://Personal/Tailscale/CasaOs Auth Key`** (note: Personal
vault, item `Tailscale`, not Homelab). It's consumed — only needed for a reinstall, and it expires
~90 days after creation; mint a new one then. Install method that kept it off disk: `op read … | ssh
homelab 'umask 077; cat > /dev/shm/ts-authkey'`, then `tailscale up --auth-key=file:/dev/shm/ts-authkey`
under sudo with an EXIT trap that shreds it.

## Checks
```
tailscale status
tailscale status --json | jq '.Self | {Tags, Online, KeyExpiry, PrimaryRoutes}'
tailscale debug prefs | jq '{AdvertiseRoutes, RunSSH, CorpDNS, RouteAll, OperatorUser}'
```
