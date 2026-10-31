# Logbook — homelab-notebook (host)

Reverse-chronological. Newest entry on top. Host-level changes (NixOS deploys, hardware, users).
Service detail goes in `../../services/<svc>/LOGBOOK.md`; project-wide log in `../../LOGBOOK.md`.

## 2026-10-31 — HA migration Phase 4 (Home Assistant → homelab-notebook)
Deployed `homeAssistant.enable = true` (HA 2026.10.4 from nixpkgs-unstable), then a second switch adding samsungtv/homekit_controller/pytapo. `/var/lib/hass` staged from casaos (uid 286); `/root/ha-cutover.sh` does the host-specific `.storage` edits. Firewall +8123/21064/1400 tcp, +1900 udp. Load 0.37, 9.7 GB available with the full stack. No failed units.

## 2026-10-30 — HA migration Phase 3
Deployed `matter.enable = true` + `vendorid = 65521` + firewall 5353/udp. `/var/lib/private/matter-server` staged from casaos (re-staged after the first crashed start). matter-server active, :5580 listening, no failed units. Backup run OK (now includes private/matter-server).

## 2026-10-30 — HA migration Phase 2
Deployed `zigbee2mqtt.enable = true` (flake.nix + home-automation.nix copied; pan_id/ext_pan_id made literals after the first start refused the `!secret` refs). `/var/lib/zigbee2mqtt` 317:317 0700 staged before the switch. Firewall +8080. No failed units. Backup run OK (mosquitto + zigbee2mqtt).

## 2026-10-30 — HA migration Phase 1 (mosquitto → homelab-notebook)
Deployed `homelab.homeAutomation.mosquitto.enable = true` (only flake.nix changed on the box). mosquitto active on 0.0.0.0/[::]:1883, `/etc/hosts` now `127.0.0.1 mosquitto`, no failed units. Created `/etc/mosquitto-secrets/` (root 0700, 3 hash files 0600). Seeded `/var/lib/mosquitto/mosquitto.db` from casaos.

## 2026-10-30 — Deployed home-automation.nix (all toggles off) + homelab-backup timer
Snapshot `~/nixos.bak-pre-homeautomation`. Copied only `flake.nix`, `flake.lock`, `home-automation.nix` to the box
(box was in sync before; `hermes.nix` drift kept on purpose). `systemd-run … nixos-rebuild switch`: OK, no failed
units; hermes-agent/pihole-ftl/tailscaled active. New: `/etc/hosts` `192.168.14.82 mosquitto`, `homelab-backup.timer`
(next 03:33), key `/var/lib/homelab-backup/id_ed25519` (root 0700). `systemctl start homelab-backup` → success,
"nothing to back up yet".

## 2026-10-30 — Home-automation modules staged (not deployed)
New `nixos/home-automation.nix` (mosquitto/zigbee2mqtt/matter-server/home-assistant, each behind
`homelab.homeAutomation.<svc>.enable`, all false), `nixpkgs-unstable` input (HA only) and build-only
output `homelab-notebook-ha-preview`. Built as `claude` in `~/ha-preview` via `systemd-run`
(unit `ha-preview-build`): EXIT=0, all substituted. GC root `~claude/ha-preview/result`. The only
change once deployed with toggles off: `/etc/hosts` gains `192.168.14.82 mosquitto`. Created
`/var/backups/ha-migration/` (root 0700) holding the latest HA backup. Box `~/nixos` untouched.

## 2026-10-28 — Pi-hole deployed (2 switches)
Added `nixos/pihole.nix` + import in `flake.nix`; copied only those two files to `~/nixos` (box
`hermes.nix` drift untouched; snapshot `~/nixos.bak-pre-pihole`). Firewall now also opens 53/tcp+udp
and 80/tcp. New root-only `/etc/pihole-secrets.env`. Switch via the documented `systemd-run` (~35 s,
all from cache). Verified pihole-ftl, hermes-agent/backend, tailscaled active; DNS answers from casaos.

## 2026-10-28 — Tailscale + `claude` user (generation 3)
`configuration.nix`: `users.users.claude` (wheel → passwordless sudo, no password/keys) and
`services.tailscale` (`openFirewall`, `extraSetFlags` `--ssh --accept-dns=false --operator=dgmneto`).
Deployed only `configuration.nix` (box kept its older `hermes.nix`; repo's undeployed hermes-restart/
polkit change left out). First `systemd-run … nixos-rebuild switch` built fine but failed activation
(`No such file or directory: 'test'` — minimal PATH); re-run with `-E PATH=…` → generation 3. Joined
tailnet with `op://Personal/Tailscale/Laptop Server Auth Key` piped via stdin (a `/dev/shm` staging
copy was wiped by logind RemoveIPC; one attempt with an empty key fell into interactive login, killed).
Verified: node `100.67.47.127` tag:server, KeyExpiry null, RunSSH, CorpDNS false; `sudo -u claude sudo
-n whoami` → root; hermes-agent/backend active; `tailscale ping` from casaos direct 3 ms. Also found:
RAM is 11.7 GB now (README said 4 GB). Not verified: Tailscale SSH login as `claude` end-to-end.

## 2026-10-28 — Repo restructure: host folder created
`notebook/` (NixOS flake + hardware models) moved here as `nixos/` + `hardware/`. No change on the box.
Pre-restructure host history (2026-10-07 emergency-mode incident, 2026-10-08 Hermes migration) is in
`../../LOGBOOK.md` and `../../services/hermes/LOGBOOK.md`.
