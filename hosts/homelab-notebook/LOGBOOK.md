# Logbook — homelab-notebook (host)

Reverse-chronological. Newest entry on top. Host-level changes (NixOS deploys, hardware, users).
Service detail goes in `../../services/<svc>/LOGBOOK.md`; project-wide log in `../../LOGBOOK.md`.

## 2026-11-15 — Rack case: rear support brackets for the Lab Rax rack
Added `rear_bracket_left.stl` / `rear_bracket_right.stl` (mirror images, ~7 cm³ each) to `hardware/case/build_case.py` (`build_rear_bracket`, constants `RACK_*`/`BRK_*`). Each is an L that bolts to the front face of a rear post's flange through the case's U holes at 6.35 and 22.225 mm, using M6 clearance holes, M6 bolts from the front and nuts behind. A 4 mm ledge reaches 20 mm past the post's inner edge, so ~19 mm runs under the case floor, and 30 mm forward. It sits 0.1 mm below the case bottom so the case rests on it and the front ears only locate it. A 2 mm brace on the lip side stays clear of the bolt heads. Exported lying on the outer face, so the L is in the layer plane. Post geometry measured by sectioning the rack's `5U Vertical Post.3mf`: flange 30 x 6, holes 7.6 mm at 22.86 mm from the outer side, Z 6.32/22.23/38.12 per U; the 7 x 5 mm lip next to the side web keeps the bracket at X >= 14.5. The ledge sits ~4 mm into the U below, at the rear corners only. Verified the hole positions by sectioning the STL; Blender reports it manifold. Render: `out/rear_bracket.png`. Not printed yet.

## 2026-11-15 — Rack case vs the Lab Rax 10" 5U printable rack (investigation)
The user will print the "Lab Rax 10in Server Rack - 5U" (files in ~/Downloads/Lab+Rax+10_+Server+Rack+-+5U/). Read from its STLs: four identical 5U posts (30 x 35 mm, 222.2 tall, 6 mm front flange with the hole pattern), 228 x 171.5 mm top and bottom panels between the posts, outer about 282 W x ~241 D. Between the posts there is ~222 mm, and our body is 220 wide. Front flange to rear flange is ~235 mm; our case is 235.2 mm behind the panel, so it ends about at the rear posts. Ears on the case's rear can't work: anything wider than 222 mm won't slide in past the front posts. Rear support has to be a separate bracket or shelf bolted to the rear posts. PLA: fine for the load with rear support, but it creeps on front-only ears and softens at ~55-60 °C near the CPU/fan exhaust. No model change.

## 2026-11-15 — Rack case: child board no longer mounted
The user will fix the I/O child board (and the USB Ethernet adapter on it) loose inside the case by hand. `build_case.py` drops its three posts and pilots, its rear-wall USB-A and audio openings, the child board from the assembly/renders, and `fit_childboard.stl`. The stale `childboard_*.png` renders are deleted. The rear cable hole stays where it was (X 183.9, now `CABLE_HOLE_EAST` from the SE post). `childboard/build_childboard.py` still builds the model, but the case no longer reads it. Verified by sectioning tray.stl: the rear wall is solid at Z 6/9 apart from the cable hole, and the floor has no posts there. Mounting check: printed parts by volume are tray ~310 g + lid ~125 g of PETG, about 0.85 kg loaded, with the centre of mass ~115 mm behind the panel. That is ~1 N·m in total on the two rack ears, about 15 N per top screw, which is fine for 2 screws per ear. Creep, not strength, is the risk: use PETG/ASA, not PLA.

## 2026-11-15 — Rack case: power button hole
The power button lives on the keyboard (28-pin, 1.0 mm FFC to the board), which won't be in the case. Plan: a 28-pin 1.0 mm same-side FFC from the board to a breakout (the user only found 30-pin ones; push the cable to one end and find the pads with continuity), and a 12 mm self-reset 1NO metal push button soldered across the two power pins. The pins are not identified yet. `build_case.py` cuts a 12.3 mm hole (`BUTTON_HOLE_D`) in the front panel at mid-height. It sits midway between the board's east edge (X 115.2) and the NE lid post (X 158.1, Z 21.8). Asserts keep an estimated 17 mm nut clear of the board, the post and the lid. Verified by sectioning tray.stl (hole X 151.95-164.25) and in the closed_front render. Not printed yet.

## 2026-11-15 — Rack case: rear Ethernet cable hole
The drop-jaw RJ45 was too hard to fit, so the user is switching to a USB 3.0 gigabit Ethernet adapter (UGREEN, USB-A) plugged into the child board's USB-A and fixed loose inside the case. The adapter is deliberately not modelled. `build_case.py` now cuts a 16 x 14 mm cable pass-through in the rear wall (`CABLE_HOLE_W/H`), centred between the child board's east end and the SE lid post (X 175.9-191.9, Z 15.1-29.1). It fits an RJ45 plug with its boot. The front-panel drop-jaw hood is still in the model, pending a decision. Verified by sectioning tray.stl and in the closed_rear_west render. Not printed yet. Open item: the power button sits on the keyboard (28-pin FFC to the board), which won't be in the case.

## 2026-11-07 — Rack case: six RJ45 height-variant fit pieces
`hardware/case/build_case.py` now also exports `out/rj45_fit_<dz>.stl` for dz = -0.5, -0.3, -0.1, +0.1, +0.3, +0.5 mm (`RJ45_FIT_DZ`). Each is fit_test cut to the RJ45 alone: the panel strip around the jack plus the H1/H2 pins (the two northmost board holes) on a triangle frame, so the board locates itself and nobody has to hold it in place. Only the hood height over the springs differs: ceiling, latch lip and pocket move by dz. The bottom of the opening stays at the springs, so a raised variant has no ledge at the entry. The dz value is raised on the H1-H2 bar. The springs height (`RJ45_PLUG_FLOOR`) is an estimate, and the winning variant corrects it. `text_mesh` helper shared with the pin gauge. Verified by sectioning: the ceiling steps 0.2 mm per variant and the opening bottom is fixed. All six are manifold, each 94.5 x 28.1 x 24 mm. fit_test.stl has the same 6 non-manifold edges it had before this change. Not printed yet.

## 2026-11-07 — Rack case: RJ45 hood sized from the proven cover
The user printed a third-party drop-jaw RJ45 cover (`~/Downloads/rj45-cover.3mf`, PrusaSlicer 2023) and it fit the real board and plug perfectly. Its inside dimensions are now the hood channel in `hardware/case/build_case.py`: width 12.5, springs to ceiling 7.15, latch slot 7.2 (were the unconfirmed estimates 12.7 / 7.4 / 7.4). Wall (2.0), lip and latch pocket unchanged. Rebuilt with Blender 5.1.2; tray.stl, rj45_test.stl, fit_test.stl and renders regenerated. Verified by sectioning rj45_test.stl: channel 12.50 x 7.15, slot 7.20. Not printed yet.

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
