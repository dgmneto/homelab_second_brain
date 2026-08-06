---
name: disk-health-storage-array
description: Failing library/footage LVM array; disk replacement to RAID1 is PAUSED mid-flight (2026-08-06) with the box powered off — read the "current state" section before touching anything
metadata:
  node_type: memory
  type: project
---

# `library` LVM array — failing disks, zero redundancy

> ## ⚠ CURRENT STATE (2026-08-06): disk replacement PAUSED mid-flight, box POWERED OFF
>
> A rolling replacement of both disks with 2× 4TB, ending on an LVM RAID1 mirror, is **half done**.
> It stopped because the replacement drives turned out to be **SAS, not SATA** — this box has an Intel
> N3350 AHCI **SATA** controller, and SAS drives are not backward-compatible (the connector has a
> bridged gap and won't seat). Waiting on SATA replacements; user expects them within days.
>
> **The box is powered off and in a stable, bootable configuration.** Nothing is broken or half-written:
>
> | | |
> |---|---|
> | `libraryLogicalVolume` | **1000 GiB** (shrunk from 3.15 TiB), entirely on `sda`, 761G used / 178G free |
> | `footageLogicalVolume` | 500 GiB, on `sda`, 41G used |
> | `/dev/sda` (`WD-WMC301625707`) | sole PV, `PFree <363.02g` — **holds all data, no redundancy** |
> | `/dev/sdb` (`WD-WMAUR0541868`) | `vgreduce`d + `pvremove`d, LVM labels wiped, empty. May or may not still be physically installed |
> | Docker | `docker.service`, `docker.socket`, `containerd.service` all **disabled** — they do NOT come back on boot |
> | `plex-qbittorrent-watchdog` | `systemd --user` unit, stopped but still `enabled` (returns on boot) |
>
> **To bring services back up meanwhile:** power on, then
> `sudo systemctl enable --now docker`, `docker compose up -d` per stack (`gluetunProtonVPN` before
> `qbittorrent`/`prowlarr`), and `systemctl --user start plex-qbittorrent-watchdog.service`.
> `/library` has 178G free, so downloads keep working; the shrink is invisible to the services.
>
> **To resume the migration:** the remaining work is Phase 2 onward — fit SATA disk N1 in the free port,
> `sgdisk -n1:0:-100M -t1:8e00`, `pvcreate`/`vgextend`, `pvmove /dev/sda` onto it, `vgreduce`/`pvremove`
> `sda`, swap `sda` → N2, `vgextend`, `lvconvert --type raid1 -m1` on **both** LVs, then
> `lvextend -l +100%FREE -r` on `library` to reclaim capacity. Full plan and rationale in the
> 2026-08-06 entry of [../LOGBOOK.md](../LOGBOOK.md). Progress helper:
> `ssh -t dgmneto@homelab 'sudo /home/dgmneto/migration-progress.sh'`.
>
> Config safety net: `/footage/services` (3.7G, 22,760 entries) tarred to the Mac at
> `~/homelab-footage-services-2026-08-05.tar`.

## Two LVM traps this migration exposed

1. **Allocated ≠ used.** The volumes held 805 GiB of data but were **100% allocated** (`VFree 0`), so
   `pvmove` was impossible — it moves *allocated extents*, not used blocks, and needed 1.82 TiB of free
   extents that didn't exist. A filesystem+LV shrink has to come first.
2. **`lvreduce` frees the LV's *highest* LEs**, which is not necessarily the disk you want emptied.
   Here `lvs -o+seg_pe_ranges` showed `libraryLogicalVolume` was laid out **`sdb` first**
   (`sdb:0-476931`, then `sda:0-348931`), so the shrink freed the *`sda`* half — which happened to be
   exactly what created room to then drain `sdb` onto `sda`. **Always read `seg_pe_ranges` before
   assuming which physical disk a shrink will empty.**

Also worth knowing: `/footage` is 44G used, but only **3.7G of that is service configs** — Docker's
data-root is `/footage/docker` (35G), plus the 18G `/footage/home/openclaw` leftover still pending
deletion. And deleting files does **not** shrink `pvmove` work, since extents move regardless.

## Historical layout (pre-migration)

The `libraryVirtualGroup` volume group (`vgs`/`pvs`) was built from **two bare spinning disks with no
RAID/mirror**:

- `/dev/sda` — WD Green `WD20EZRX-00DC0B0`, ~57,790 power-on hours (~6.6y). Holds `footageLogicalVolume`
  (`/footage`, 500G) alone, plus half of `libraryLogicalVolume`.
- `/dev/sdb` — WD RE4 `WD2003FYYS-05T8B0`, ~127,584 power-on hours (~14.6y — very old). Holds the other
  half of `libraryLogicalVolume` (`/library`, 3.15T, concatenated across both disks).

Both are `linear`/concatenated, not mirrored — **either disk failing takes down its LV entirely**, and
since `footageLogicalVolume` (service configs) lives solely on `sda`, an `sda` failure = every service
config gone, not just media.

## 2026-08-03 incident: 13-day silent hang

`smartd` logged pending sectors on both disks (`sda`: 1, `sdb`: 2) at `Jul 21 16:39:13`, then the
journal went **completely silent for 13 days** — no clean shutdown, no crash dump, just nothing until
the box was found unresponsive (ping/ARP dead) on 2026-08-03 and physically power-cycled. Root cause:
a read hit a bad/pending sector, the kernel/LVM I/O hung waiting on it, and the whole box froze solid
(not a panic, not an OOM — just wedged). No amount of SSH/network troubleshooting helps this case:
the host is fully unresponsive at L2 (ARP shows `incomplete`), so the only recovery is a physical power
cycle. See [[ssh-access]] for the access path used to investigate once it came back.

Check current SMART state:
```
ssh dgmneto@homelab
sudo smartctl -a /dev/sda | grep -E 'Pending|Reallocated|Uncorrectable|Power_On_Hours'
sudo smartctl -a /dev/sdb | grep -E 'Pending|Reallocated|Uncorrectable|Power_On_Hours'
```

SMART as of 2026-08-05: `sda` 57,842 h, **Current_Pending_Sector 3** (was 1 on 2026-08-03 — actively
growing); `sdb` 127,636 h, pending 2, unchanged. Both `PASSED`, 0 reallocated, 1 offline-uncorrectable
each.

## Open risk until the migration finishes

All data now lives on `sda` alone — the disk whose pending-sector count is climbing — with no
redundancy at all. That is the intended intermediate state of the migration, but it was meant to last
hours, not days. While it persists:
- Don't stall. Finish Phase 2+ as soon as SATA disks arrive.
- If the wait stretches past ~a week, consider a stopgap: `vgextend` the old `sdb` back in and
  `lvconvert --type raid1 -m1` both LVs (1.5 TiB fits on `sdb`'s 1.82 TiB). Two dying disks mirrored
  beats one dying disk alone — at the cost of a ~4h sync that stresses both.
- Re-run the `smartctl` check above periodically — a rising pending-sector count means the drive is
  actively degrading, not just old.
