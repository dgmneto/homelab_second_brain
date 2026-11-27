# Logbook — homelab-notebook (host)

Reverse-chronological. Newest entry on top. Host-level changes (NixOS deploys, hardware, users).
Service detail goes in `../../services/<svc>/LOGBOOK.md`; project-wide log in `../../LOGBOOK.md`.

## 2026-11-26 — Deploy: pytapo 3.4.31 → 3.4.32
Box vs repo diff: only that change (+ known hermes.nix drift). Box backup `home-automation.nix.bak-pre-pytapo32-20261126`. systemd-run switch OK
(50 s); HA restarted 13:09:57, z2m not restarted.

## 2026-11-26 — Deploy: HA extraComponents += shelly
Box vs repo diff before deploy: only the known hermes.nix drift + .bak files. Copied home-automation.nix (box backup
`home-automation.nix.bak-pre-shelly-20261126`), systemd-run switch succeeded in 30 s (HA env already had aioshelly; HA not restarted by the switch).

## 2026-11-24 — Deploy: z2m serial.port → SLZB-MR5U; repo synced to box
`home-automation.nix` on the box was **ahead of the repo** (boot guards for z2m/matter-server chip.json, wake_on_lan/ping, pytapo 3.4.31
were never committed). Edited the box copy (z2m `serial.port` → `tcp://192.168.11.121:6638`), deployed twice with the systemd-run switch
(the first run had an unchanged file after a failed sed edit), then copied the box file into the repo. hermes.nix drift left as is (repo ahead,
known). Backup of the pre-change file: `~/nixos/home-automation.nix.bak-pre-mr5u-20261124`.

## 2026-11-16 — Rack case: both west posts float, shorter; Ethernet jack opening
`hardware/case/build_case.py`:
- **Floating posts.** The NW lid post now floats like the SW one. Both come from `floating_post()`: a 7 x 7 column hung off the west wall and the south wall / front panel, with a 45 deg wedge underside.
- **Shorter.** The posts are now `FLOAT_POST_H` = 10 mm (wedge 7 + 3 straight), down from ~14.5, so the tip sits at Z 31.7. Asserts keep them 1 mm clear of the fan top and of the board's tallest part, and tall enough for the wedge.
- **Ethernet jack opening.** At the user's request, the front panel now has a through opening around the board's drop-jaw jack instead of being closed. The former inner `rj45_jack_pocket` now runs through the panel: X 19.2-36.4, Z ~20.7 to frame top + 0.3. There is still no hood, so nothing holds a plug down on the springs.

Rebuilt: tray.stl and tray_rig.stl are manifold. Checked in renders: the front shows the jack through the new opening, and both west corner posts are short wedges. Not printed yet.

## 2026-11-16 — Rack case: tray_rig.stl, whole-tray skeleton test print
The user wanted one quick test print that covers everything, not just the fan. `build_tray_rig` in `hardware/case/build_case.py` intersects the real tray, at full height, with keep volumes. It keeps:
- all 7 board standoffs + pins
- both fan posts + pins
- the 4 drive screw holes (floor discs with counterbores)
- the front panel strip from the west wall to past the power button (ports, RJ45 jack pocket, button hole), cut off 3 mm above the highest opening
- the SW corner: west wall with the fan exhaust grill, a bit of south wall, and the floating post.

The pieces are tied together by strips of the tray's own floor: a minimum spanning tree over the anchors, plus each node's next-nearest link. The strips are part of the same intersect, so there are no coplanar unions. A first try with a separately unioned bar frame gave 26 non-manifold edges.

Result `out/tray_rig.stl`: ~60 cm³ against ~240 cm³ for the full tray, footprint ~180 x 238 mm. Board, fan and drive all mount at their real positions. Manifold. Checked in renders with and without the board/fan models. Not printed yet. `fan_rig.stl` stays as the smaller fan-only check.

## 2026-11-16 — Rack case: fan on pins + fan_rig.stl test print
`hardware/case/build_case.py`: the fan's two posts now end in chamfered pins (`FAN_PIN_D` 2.55 mm, 4 mm tall) through its 2.7 mm holes instead of M2.5 pilot holes, so no screws; the fan drops on like the board. The diameter copies the board's 0.16 mm undersize (PIN_D 3.40 in 3.56 holes). New quick test print `out/fan_rig.stl` (`build_fan_rig`, ~77 x 90 mm footprint, 13.5 mm tall, 164 kB). It has the two fan posts + pins and the board's H4/H7 standoffs + pins (the holes the fan was triangulated against) on a 2 mm bar frame, everything lowered by the same amount (fan posts 3 mm). The board drops on H4/H7 and the fan on its pins. That checks the fan pin fit, the fan's position against the board, and the fan top being flush with the board top. Verified in a render with the board and fan models in place; tray and rig export manifold. Not printed yet.

## 2026-11-16 — Rack case: tray fixes after the first full print
Feedback from the user's first tray print, applied in `hardware/case/build_case.py`:
- **SSD bosses removed.** The drive now sits flat on the floor (Z 2.5-12.0), with counterbored M3 holes straight through the 2.5 mm floor (`DRIVE_BOSS_*` gone). That leaves ~1 mm of floor under each screw head, so use thin-head drive screws.
- **SW lid post floats above the fan.** The full-height SW corner post collided with the blower. It is now `sw_post()`: a 7 x 7 column hung off the west and south walls from 1 mm above the fan top (`SW_POST_CLEAR`, Z 27.1) up to the lid, with a 45 deg wedge underside rising east from the west wall, so it prints without support. An assert guards room for it. The lid-screw pilot breaks through the wedge underside, which is harmless.
- **RJ45 hood removed.** The hood, its channel/latch cuts, `rj45_test.stl`, `rj45_fit_*.stl` and their renders are deleted, along with the `RJ45_*` hood constants. The front panel is now closed over the jack. Only the inner pocket for the board's jack housing remains, leaving ~0.7 mm of panel skin in front of it.
Rebuilt: tray.stl is manifold; fit_test.stl keeps its 4 pre-existing non-manifold edges. Checked in a SW-corner render and a front render: the post clears the fan, and the panel shows only power/HDMI/USB openings. Not reprinted yet.

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

## 2026-11-15 — Link speed check: cable/port fault + more reboots (investigation)
The box was up again at 21:47 after another reboot (`/proc/uptime` 98 s, so it booted ~21:45:30). Readings: `enp2s0` (Realtek RTL8168h, r8169) 1000/full; casaos `enp3s0` 1000/full; ping between them 0.49 ms avg, 0% loss over 20 pings. But kernel log this boot: `Downshift occurred from negotiated speed 1Gbps to actual speed 100Mbps, check cabling!`, so the link came up at **100 Mbps (downshifted)**. Then at 21:46:52 `Link is Down`, 21:47:01 `Link is Up - 1Gbps/Full`. `carrier_changes`=4 within 98 s of uptime. A downshift means fewer than 4 working pairs: a bad cable, a damaged RJ45 or one not fully seated (the new rack case's RJ45 hood is a suspect), or a bad switch port. It went unreachable again within ~1 minute (SSH timed out mid-command). No throughput test was possible: iperf3 isn't installed on either box, and the host didn't stay up. Note: the cable fault explains the link flaps but not the hard reboots; both together suggest physical disturbance or power. Check: reseat/replace the cable, try another switch port, check the charger.

## 2026-11-15 — Back briefly at 21:42, then dropped again (investigation, unstable)
Rechecked about 1h after the entry below. The box was back: Tailscale pong via DERP, LAN ping OK, MAC `08:8f:c3:96:1a:67` on `enp2s0` (now in the README). Previous boot `-1` ended **abruptly at 21:29:13 with no shutdown messages** (z2m was mid-start), so a hard power loss, reset or crash. It had also been running without DNS (hermes: Telegram "Name or service not known"). The new boot came up with the clock at 1 Jan (the RTC loses time) and NTP synced it later. HA, z2m, mosquitto, matter-server, tailscaled, hermes-agent and pihole-ftl were all active, but the system was `degraded` because `pihole-ftl-setup` failed at boot (no DNS yet). Not restarted: the action was declined as out of scope for a check-only task. **About 1 minute later it dropped off the LAN again** (ARP PROBE, no ping), and it was still down 4 minutes later at 21:46. Pattern: repeated hard crashes or power losses. Suspect power (charger/PSU, or a battery that is missing or dead: no `power_supply` status was readable) or overheating in the new rack case. Needs physical inspection. No change made.

## 2026-11-15 — Unreachable: off Tailscale and off the LAN (investigation)
Checked from a cloud session. `tailscale status` showed the node offline, last seen ~4h earlier. `tailscale ping` and `ssh claude@homelab-notebook` both timed out. From casaos (`ssh claude@casaos`): `ping 192.168.11.21` gave Destination Host Unreachable, `ip neigh` showed FAILED (no ARP reply), and ports 22/8123 had no route. A ping sweep of 192.168.11.0/24 followed by a port 22/8123/1883 probe found no host that looks like it moved to a new DHCP address. Port 22 was open on .51/.71/.223/.244, but those are dropbear or Ubiquiti devices, not NixOS OpenSSH. Conclusion: the box is powered off, suspended, crashed, or off the network (no link). It needs physical attention. No change made.
Gotcha recorded: the NIC MAC is not in this repo, so a moved DHCP lease can't be identified from casaos' ARP table. Add it to the README next time the box is up (`ip link`).

## 2026-11-10 — Deploy: tapo_control dependencies
home-automation.nix: extraComponents +onvif/ffmpeg/stream; extraPackages: pytapo override 3.4.30, python-kasa. Box copy
diffed first (only these changes); backup `home-automation.nix.bak-pre-tapo-20261110`. Switch OK at 21:04; HA verified.

## 2026-11-10 — Deploy: octopus_energy off Nix, pydantic added, z2m blocklist
home-automation.nix: `customComponents = [ ]` (octopus_energy now HACS-managed), `pydantic` in HA `extraPackages`, z2m
`settings.blocklist` for 3 retired AVATTO TRVs. Box copy diffed (only hermes.nix drift, untouched); backup
`~dgmneto/nixos/home-automation.nix.bak-pre-octopus-hacs-20261110`. Switch via systemd-run: OK in 1m12s. Then copied the Nix 19.2.1
octopus tree into `custom_components/octopus_energy` as a writable dir, and restarted HA so HACS can update it.

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
