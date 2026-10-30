# homelab-notebook — NixOS host (added 2026-10-08)

Second host. Runs [hermes](../../services/hermes/README.md), [pihole](../../services/pihole/README.md) (tailnet DNS, ports 53 + 80) and, since 2026-10-30, [mosquitto](../../services/mosquitto/README.md) (1883) + [zigbee2mqtt](../../services/z2mqtt/README.md) (8080) + [matter-server](../../services/matter/README.md) (5580; HA-stack migration in progress, see [MIGRATION.md](../../services/homeassistant/MIGRATION.md)) natively (no Docker). Nightly `homelab-backup.timer` pushes HA-stack state to casaos. Hermes can SSH to
[casaos](../casaos/README.md) as user `hermes` (docker group, no sudo) and **pushes to this repo**,
so `git pull --rebase` before editing.

Layout:
- [nixos/](nixos/) — the system flake (`configuration.nix`, `hardware-configuration.nix`, `hermes.nix`, `pihole.nix`, `home-automation.nix` — HA stack staged, all toggles off; see
  [MIGRATION.md](../../services/homeassistant/MIGRATION.md)). Inputs include `nixpkgs-unstable` (HA only) and a
  build-only output `homelab-notebook-ha-preview` — never `switch` to it.
  **This is the deploy source** (imported from the old `notebook_home_lab` repo, history kept; that repo
  is no longer checked out on the Mac).
- [hardware/](hardware/) — Blender scripts + printable outputs: `board/`, `childboard/`, `fan/`, and
  `case/` (10-inch 1U rack case; `case/build_case.py` reads its siblings via `HERE/..`, so keep the four
  dirs together). `hardware/photos/` holds source photos; `*.HEIC` are gitignored, local only.
- [LOGBOOK.md](LOGBOOK.md) — host-level changes (OS, NixOS deploys, hardware).

## Hardware

`192.168.11.21` (DHCP — reserve it on the router), Acer Aspire A315-34, Celeron N4020 (2 cores),
4 GB soldered RAM + SO-DIMM slot now populated (**11.7 GB total** per `free -m`, 2026-10-28; slot max 12 GB), 1 TB 5400 rpm HDD (partitions labelled
`HL-BOOT`/`HL-SWAP`/`HL-ROOT`). NixOS 26.05, **no Docker** — services are native NixOS modules.

## Access

```
ssh homelab-notebook        # dgmneto, ed25519 key that exists ONLY in 1Password ("homelab-notebook SSH")
```
- Key-only SSH, no passwords, no root login; `dgmneto` has **passwordless sudo**.
- **Tailscale** (since 2026-10-28): node `homelab-notebook` / `100.67.47.127`, `tag:server`, Tailscale SSH.
  User **`claude`** (wheel → passwordless sudo, no password/keys) is for agents: Claude cloud sessions
  `ssh homelab-notebook` as `claude` via the tailnet — no 1Password needed. Details:
  [services/tailscale](../../services/tailscale/README.md#homelab-notebook-node).
- **If 1Password is locked, you are locked out** — there is no `id_rsa` fallback on this host. Agents
  running while the user is away cannot reach it. (The Bash sandbox also can't reach the 1Password
  agent socket; run ssh/op commands with the sandbox disabled.)
- Config is the flake in this repo at `hosts/homelab-notebook/nixos/`. Deploy: rsync that dir to
  `homelab-notebook:nixos/`, then `sudo nixos-rebuild switch --flake path:.#homelab-notebook` in `~/nixos`.
  **Always `git diff` before deploying** — other sessions edit it too (a 2026-10-07 label change
  deployed unreviewed left the box in emergency mode; root is locked, so recovery needs the console +
  picking the previous generation in the systemd-boot menu).
- Builds are RAM-bound (4 GB + swap on HDD): big builds can take ~1 h and may push the box into heavy
  swap; if `nix-daemon` balloons, kill the build + `sudo systemctl restart nix-daemon` (progress kept).
  Run switches under `systemd-run` so an SSH drop can't kill them mid-activation. **Pass a PATH** —
  systemd-run's default PATH has none of NixOS's bin dirs, and nixos-rebuild-ng then dies at activation
  with `[Errno 2] No such file or directory: 'test'` (build succeeds, switch doesn't happen). Verified:
  ```
  cd ~/nixos && sudo systemd-run --wait --collect --unit=nixos-switch \
    -E PATH=/run/wrappers/bin:/run/current-system/sw/bin -p WorkingDirectory=$HOME/nixos \
    nixos-rebuild switch --flake path:.#homelab-notebook
  ```
- **As `claude`** you can't `cd ~dgmneto/nixos` (home is 0700): copy files with `… | ssh homelab-notebook "sudo -u dgmneto tee /home/dgmneto/nixos/<f>"`
  and run commands there via `sudo -u dgmneto bash -c 'cd ~/nixos && …'`; the `systemd-run` switch above works as-is with
  `-p WorkingDirectory=/home/dgmneto/nixos`. Pre-pihole snapshot of the box copy: `/home/dgmneto/nixos.bak-pre-pihole`.
- **Repo ↔ box drift (2026-10-28):** repo `nixos/hermes.nix` has a `hermes-restart` helper + polkit rule
  that has **never been deployed** — the box's `~/nixos/hermes.nix` is the older version, and the
  2026-10-28 Tailscale and Pi-hole deploys kept the box copy on purpose (all other files are in sync). Review before the next full deploy
  (`diff` box vs repo first).

