---
name: ssh-access
description: How to SSH into the homelab server when the 1Password agent breaks key signing
metadata:
  node_type: memory
  type: reference
---

# SSH access (1Password agent bypass)

Homelab = x86_64 Debian 12 (bookworm) box at `192.168.11.13` (hostname `homelab`, internal name
`casaos`). **Not** a Raspberry Pi despite the SD-card root (`/dev/mmcblk0p2`, 27G). Bulk data on LVM:
`/library` (3.1T) and `/footage` (492G). Services = docker compose stacks; deployment repo on the
server at `/home/dgmneto/homelab` → GitHub `dgmneto/homelab`.

`~/.ssh/config` sets `Host * IdentityAgent <1Password agent.sock>`. When the 1Password agent is
locked/dead, key signing fails with `sign_and_send_pubkey: signing failed for RSA ... communication
with agent failed` → `Permission denied (publickey)`. The server accepts the RSA key fine; only the
agent signer is broken.

Workaround — bypass the agent, use the key file directly:
```
ssh -o IdentityAgent=none -o IdentitiesOnly=yes -i ~/.ssh/id_rsa dgmneto@homelab
```
For the `openclaw` deployment user, add `-o User=openclaw`. The sudo password for dgmneto is held by
the user; pipe via `sudo -S` for non-interactive use. Note: this `id_rsa` is the **homelab server**
key — it is NOT authorized on GitHub (GitHub uses the 1Password-held `ED25519` key, so pushes still
need the agent unlocked).

Related: [[footage-disk-leak]].
