# Home-automation stack: casaos (Docker) → homelab-notebook (NixOS)

Moves `mosquitto`, `z2mqtt`, `matter-server` and `homeassistant` off casaos, **one service per phase**,
in dependency order. Each cutover is ~seconds to minutes of downtime for that service and has a
rollback (casaos containers are stopped, never deleted, until Phase 5).

Config: [`hosts/homelab-notebook/nixos/home-automation.nix`](../../hosts/homelab-notebook/nixos/home-automation.nix)
— one toggle per phase under `homelab.homeAutomation.<svc>.enable`, all `false` until that phase.
Flake output `homelab-notebook-ha-preview` = everything enabled, **build-only** (never switch to it).

## Status

| Phase | Service | State |
|---|---|---|
| 0 | groundwork | **done 2026-10-30** (DHCP reserved, nightly backup to casaos live) |
| 1 | mosquitto | not started |
| 2 | zigbee2mqtt | not started |
| 3 | matter-server | not started |
| 4 | home-assistant | not started |
| 5 | decommission on casaos | not started |

## Phase 0 findings (verified 2026-10-30 from the laptop)

- **Reachability from `homelab-notebook` (192.168.11.21):** TCP OK to the coordinator
  `192.168.11.228:6638` (SLZB-06M) and to every casaos endpoint (`192.168.14.82:1883`,
  `192.168.15.25:5580`, `192.168.14.73:8123`, `192.168.14.96:8080`), so .11 ↔ .14/.15 is routed.
- **IPv6:** `enp2s0` has `fd00::/64` addresses, and the router advertises a route to
  `fde9:b6c5:757::/64` via `fe80::67:28bc:f5ae:b3b6` (MAC `c4:f7:c1:…`). That looks like a **Thread border
  router's mesh prefix**, which is what Matter-over-Thread needs. Not yet proven with a real Matter
  device: `avahi-browse` isn't installed. Before Phase 3 run
  `nix shell nixpkgs#avahi -c avahi-browse -rt _matter._tcp` and `ping -6` one device's address.
- **Versions** (casaos → nixpkgs): HA **2026.10.4** (nixos-26.05 has only 2026.5.4 → HA comes from
  `nixpkgs-unstable`, which has 2026.10.4 exactly); zigbee2mqtt 2.14.2 = 2.14.2; mosquitto 2.1.2 =
  2.1.2; python-matter-server 8.1.2 = 8.1.2. All exact matches, so no data migrations happen at cutover.
- **Sizes:** HA config 609M (80M recorder DB, 280M backups), z2m 26M, mosquitto 732K, matter 1.3M.
- **Laptop headroom:** 11.7 GB RAM (1.2 GB used), 399 GB free on `/`, load ~0.1.

## Gotchas the NixOS modules impose (designed around in home-automation.nix)

- **zigbee2mqtt module overwrites `configuration.yaml` on every start** (`ExecStartPre cp`). So the
  device list and secrets must live outside it: `devices.yaml`, `groups.yaml` and `secret.yaml`
  (`mqtt_password`, `network_key`, `pan_id`, `ext_pan_id`) in `/var/lib/zigbee2mqtt`.
- **Broker hostname:** HA's MQTT entry (`broker: mosquitto`) and z2m (`mqtt://mosquitto:1883`) use the
  old Docker DNS name. The module maps `mosquitto` in `/etc/hosts` → casaos `192.168.14.82` until Phase
  1, then `127.0.0.1`. **Neither app's config needs editing for the broker move.**
- **matter-server** runs with `DynamicUser`; state is `/var/lib/private/matter-server` (copy the casaos
  `/data` contents there, minus `credentials/` which the module keeps in its cache dir).
- **HA custom components:** the module only prunes *symlinks* in `custom_components`, so copied dirs
  (`hacs`, `espsomfy_rts`, `zoned_heating`) survive. Nix HA can't pip-install, so their requirements are
  in `extraPackages`. `octopus_energy` comes from nixpkgs. On casaos both **`octopus_energy` and
  `tapo_control` have config entries but no code folder**. Phase 4 restores octopus_energy; tapo_control
  isn't in nixpkgs: redownload it via HACS after Phase 4 and add `pytapo` to `extraPackages` if it complains.
- **HA `http.trusted_proxies`** is `192.168.14.34` (nginxIntern) + `172.21.0.83` (a Docker-bridge IP).
  From the laptop, the proxies arrive over the LAN, so add **`192.168.14.33`** (nginxProd) before Phase 4.
  The bridge IP becomes irrelevant.
- **HomeKit bridge** ("HASS Bridge") listens on **21064**; its pairing state is in `.storage`, so it
  survives the move if mDNS works. Firewall opens 21064/tcp and 5353/udp.
- **casaos `restart: always`**: a merely `stop`ped container comes back on the next casaos reboot. Use
  `docker compose down` for anything cut over. **Two z2m instances on the coordinator = Zigbee chaos.**

## Runbooks

General deploy: per [hosts/homelab-notebook/README.md](../../hosts/homelab-notebook/README.md) (git diff,
diff box vs repo, `systemd-run` switch). Pre-build first:
`nix build path:.#nixosConfigurations.homelab-notebook-ha-preview.config.system.build.toplevel`.

**Phase 1 — mosquitto.** For each user in casaos `/footage/services/mosquitto/config/passwd`
(`zigbee2mqtt`, `homeassistant`, `dgmneto`), write the hash part (after `user:`) to
`/etc/mosquitto-secrets/<user>.hash` on the laptop (root, 0600, readable by mosquitto). Set
`mosquitto.enable = true` and deploy: the hosts entry flips to `127.0.0.1`, but casaos' containers still
use Docker DNS. Then point HA's MQTT entry at `192.168.11.21` and z2m's `mqtt.server` at
`mqtt://192.168.11.21:1883` on casaos, `docker restart z2mqtt` (it republishes ~253 discovery configs), and
check that no Zigbee entities are `unavailable`. Rollback: revert those two settings.

**Phase 2 — zigbee2mqtt.** `docker compose down` z2mqtt on casaos. Copy `/footage/services/z2mqtt/data`
to `/var/lib/zigbee2mqtt` (incl. `database.db`, `coordinator_backup.json`, `state.json`,
`external_converters/`). Split the `devices:`/`groups:` blocks into `devices.yaml`/`groups.yaml`, the
four secrets into `secret.yaml`, chown to `zigbee2mqtt`. Enable and deploy. Check: the UI on
`:8080` shows ~26 devices and a light toggles. Repoint nginxIntern's z2m host. Rollback: stop the
laptop service, `docker compose up -d` on casaos.

**Phase 3 — matter.** First prove mDNS/IPv6 (see findings). Stop casaos `matter-server`; keep an
untouched dated copy of `/footage/services/matter/data`; copy it into `/var/lib/private/matter-server`;
enable and deploy; change HA's Matter URL to `ws://192.168.11.21:5580/ws`. Rollback: from the untouched copy.

**Phase 4 — Home Assistant.** Fix `trusted_proxies`. `docker compose down` HA on casaos, final rsync of
`/footage/services/homeassistant/config` → `/var/lib/hass` (chown `hass`), enable and deploy. Repoint
nginxIntern + nginxProd upstreams `192.168.14.73:8123` → `192.168.11.21:8123`. Then fix tapo_control
via HACS.

**Phase 5.** Everything `down` on casaos (not just stopped), README/service-map updates, archive the
`/footage/services/*` dirs after ~1 week.

## Backups (live since 2026-10-30)

`homelab-backup.service` on the laptop (timer 03:23 nightly ±20 min, `Persistent`) rsyncs whichever of
`/var/lib/{hass,zigbee2mqtt,mosquitto,private/matter-server}` exist to casaos over the **plain LAN**
(`192.168.11.13`, no Tailscale needed: same network) as `nbbackup`, key `/var/lib/homelab-backup/id_ed25519`.
- casaos side: system user `nbbackup` (uid 998), home = `/footage/backups/homelab-notebook` (0700, on RAID1);
  `authorized_keys` forces `/usr/bin/rrsync -wo /footage/backups/homelab-notebook`, `restrict`,
  `from="192.168.11.21"`. Verified 2026-10-30: writes OK, **read-back, `../../` escape and shell all refused**.
- Layout: `current/` = mirror; `history/<YYYY-MM-DD>/` = files changed or deleted that night (rrsync maps the
  absolute `/current/` and `--backup-dir=/history/…` inside its root, as verified). Pruned after 14 days
  by casaos `/etc/cron.d/homelab-notebook-backup` (05:41).
- Until Phase 1 it logs `nothing to back up yet` (verified). **Restore:** files are owned by `nbbackup`
  on casaos; `rsync` them back as root and `chown` to the service user (`hass`, `zigbee2mqtt`,
  `mosquitto`; matter-server is DynamicUser, so just stop it and copy into `/var/lib/private/matter-server`).
- Quirk: an `nbbackup` login started a PulseAudio user session that wrote `~/.config/pulse` into the backup
  dir (deleted; harmless if it reappears).

## Open items

1. ~~DHCP reservation~~ for `192.168.11.21`: done by the user 2026-10-30 (laptop still leases .21 from 192.168.11.1, 24h lease).
2. ~~Backup~~: done, see above.
3. An off-host copy of the latest HA backup is at `homelab-notebook:/var/backups/ha-migration/`.
4. Check for a `permit_join` complaint at Phase 2: the NixOS z2m module emits `permit_join: false`, which z2m 2.x removed.
