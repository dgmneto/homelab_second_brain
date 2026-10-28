# homelab-notebook — NixOS host (added 2026-10-08)

Second host. Runs [hermes](../../services/hermes/README.md) natively (no Docker). Hermes can SSH to
[casaos](../casaos/README.md) as user `hermes` (docker group, no sudo) and **pushes to this repo**,
so `git pull --rebase` before editing.

Layout:
- [nixos/](nixos/) — the system flake (`configuration.nix`, `hardware-configuration.nix`, `hermes.nix`).
  **This is the deploy source** (imported from the old `notebook_home_lab` repo, history kept; that repo
  is no longer checked out on the Mac).
- [hardware/](hardware/) — Blender scripts + printable outputs: `board/`, `childboard/`, `fan/`, and
  `case/` (10-inch 1U rack case; `case/build_case.py` reads its siblings via `HERE/..`, so keep the four
  dirs together). `hardware/photos/` holds source photos; `*.HEIC` are gitignored, local only.
- [LOGBOOK.md](LOGBOOK.md) — host-level changes (OS, NixOS deploys, hardware).

## Hardware

`192.168.11.21` (DHCP — reserve it on the router), Acer Aspire A315-34, Celeron N4020 (2 cores),
4 GB soldered RAM + one **empty** SO-DIMM slot (max 12 GB), 1 TB 5400 rpm HDD (partitions labelled
`HL-BOOT`/`HL-SWAP`/`HL-ROOT`). NixOS 26.05, **no Docker** — services are native NixOS modules.

## Access

```
ssh homelab-notebook        # dgmneto, ed25519 key that exists ONLY in 1Password ("homelab-notebook SSH")
```
- Key-only SSH, no passwords, no root login; `dgmneto` has **passwordless sudo**.
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
  Run long switches via `sudo systemd-run --wait ...switch-to-configuration switch` so an SSH drop can't
  kill them mid-activation.

