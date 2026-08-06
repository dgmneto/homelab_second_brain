---
name: disk-health-storage-array
description: Failing library/footage LVM array; disk replacement to RAID1 is PAUSED mid-flight (2026-08-06) with the box powered off — read the "current state" section before touching anything
metadata:
  node_type: memory
  type: project
---

# `library` LVM array — failing disks, zero redundancy

> ## ⚠ CURRENT STATE (2026-08-06): disk replacement PAUSED, running on ONE disk
>
> A rolling replacement of both disks with 2× 4TB, ending on an LVM RAID1 mirror, is **half done**.
> It stopped because the replacement drives turned out to be **SAS, not SATA** — this box (a ZimaBlade,
> Intel Apollo Lake) has an AHCI **SATA** controller, and SAS is not backward-compatible: SATA drives
> run on SAS controllers, never the reverse, and the SAS connector's bridged gap won't even seat in a
> SATA cable. Passive "SAS→SATA adapters" sold online do **not** bridge the protocol — they adapt
> connectors for the *opposite* direction. A SAS HBA (LSI 9207-8i etc.) would work electrically but the
> ZimaBlade's ~36–60W USB-C PD budget cannot feed an HBA plus two 3.5" enterprise drives, which also
> need external power. Correct fix: SATA drives. Replacements ordered 2026-08-06.
>
> **The box is powered on and fully in service on the single remaining disk** — all 21 containers up.
> Nothing is broken or half-written:
>
> | | |
> |---|---|
> | `libraryLogicalVolume` | **1000 GiB** (shrunk from 3.15 TiB), entirely on `sda`, 761G used / 178G free |
> | `footageLogicalVolume` | 500 GiB, on `sda`, 41G used |
> | `/dev/sda` (`WD-WMC301625707`) | sole PV, `PFree <363.02g` — **holds all data, no redundancy** |
> | `/dev/sdb` (`WD-WMAUR0541868`) | `vgreduce`d + `pvremove`d, LVM labels wiped, empty. May or may not still be physically installed |
> | Docker | re-enabled 2026-08-06; all 21 containers running |
> | `plex-qbittorrent-watchdog` | `systemd --user` unit, running again |
>
> **Interim hardening added while single-disk (keep after the mirror exists):**
> - **Hardware watchdog enabled** — `wdat_wdt` via `/etc/systemd/system.conf.d/10-watchdog.conf`
>   (`RuntimeWatchdogSec=60`). A total freeze like 2026-07-21 now self-reboots in ~1 min instead of
>   sitting dead for 13 days.
> - **`eh_deadline` does NOT work on this box** — writes to
>   `/sys/class/scsi_host/host*/eh_deadline` return `Invalid argument` because libata/AHCI uses its own
>   error handler, not SCSI EH. It is also *not* a block-device attribute (`/sys/block/sd*/device/…`
>   doesn't exist here). Don't re-add that udev rule; the watchdog is the working substitute.
> - **smartd now actually alerts.** It was `DEVICESCAN … -m root -M exec …/smartd-runner` with **no MTA
>   installed**, so the 2026-07-21 pending-sector warnings went nowhere — that silence is the real
>   reason a bad sector became a 13-day outage. Now runs `/usr/local/sbin/smart-alert.sh`, which logs to
>   `/var/log/smart-alerts.log` + journal (`daemon.crit`) and sends Telegram via the hermes bot, reading
>   `TELEGRAM_BOT_TOKEN`/`TELEGRAM_ALLOWED_USERS` from `/footage/services/hermes/config/.env` **at run
>   time** (no secret literals on disk or in this repo).
>
> **Watch `/library` free space:** it is 984G instead of 3.1T until Phase 3 re-extends it, so the arr
> stack will fill it far sooner than usual (178G free at the pause).
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
