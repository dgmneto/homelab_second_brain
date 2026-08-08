---
name: disk-health-storage-array
description: The library/footage LVM array is now an LVM RAID1 mirror on two new 4TB disks (2026-08-08); how it is laid out, how to check it, and the LVM traps the migration exposed
metadata:
  node_type: memory
  type: project
---

# `library` LVM array — RAID1 mirror on 2× 4 TB (since 2026-08-08)

`libraryVirtualGroup` is now **mirrored**. Both logical volumes are `--type raid1 -m1` across two
physical volumes on two different disks, so a single disk failure no longer takes anything down.

| | |
|---|---|
| `/dev/sda1` | **TOSHIBA MG08ADA400E**, serial `12J0A036FXBG`, 4 TB, 7200 rpm, 23,819 h |
| `/dev/sdb1` | **HGST HUS724040ALA640** (Ultrastar 7K4000), serial `PN1334PEJ2ZESS`, 4 TB, 7200 rpm, 35,221 h |
| `libraryLogicalVolume` | **3.15 TiB**, `/library`, mirrored |
| `footageLogicalVolume` | 500 GiB, `/footage`, mirrored |

Both disks are recertified (ServerPartDeals) but were verified clean before any data was trusted to
them: 0 reallocated, 0 pending, 0 offline-uncorrectable, 0 UDMA CRC errors on both. Both are exactly
4,000,787,030,016 bytes, and each is partitioned with `sgdisk -n1:0:-100M -t1:8e00` — the 100 MiB of
end-slack exists so a future replacement drive that is marginally smaller still fits the mirror.

Retired 2026-08-08 and shelved: `WD-WMAUR0541868` (WD RE4, 14.6 y) and `WD-WMC301625707` (WD Green,
3 pending sectors and climbing). The 2026-07-21 → 08-03 13-day silent hang came from the latter class
of failure; see the history section below.

## Checking it

```
ssh dgmneto@homelab
sudo lvs -a -o name,attr,size,sync_percent,raid_sync_action,devices libraryVirtualGroup
sudo pvs
sudo smartctl -a /dev/sda | grep -E 'Pending|Reallocated|Uncorrectable|Power_On_Hours'
sudo smartctl -a /dev/sdb | grep -E 'Pending|Reallocated|Uncorrectable|Power_On_Hours'
```

Healthy looks like: each LV `rwi-aor---` with `Cpy%Sync 100.00` and `SyncAction idle`, and each LV's
`_rimage_0` / `_rimage_1` on **different** PVs. A leg letter of `I` (capital, as in `Iwi-aor---`) means
that image is *out of sync*; lowercase `i` means in sync. A `p` (partial) attribute means a PV is
missing — that is the real "a disk died" signal.

**Untested:** nobody has actually pulled a disk to confirm failover behaves. Redundancy currently rests
on `lvs` reporting two in-sync legs, not on an observed degraded-mode survival.

## Monitoring (added 2026-08-06, keep it)

- **Hardware watchdog** — `wdat_wdt` via `/etc/systemd/system.conf.d/10-watchdog.conf`
  (`RuntimeWatchdogSec=60`). A total kernel freeze now self-reboots in ~1 min instead of sitting dead
  for 13 days.
- **`eh_deadline` does NOT work on this box.** It is a SCSI *host* attribute
  (`/sys/class/scsi_host/host*/eh_deadline`), not a block-device one, and libata/AHCI rejects writes
  with `Invalid argument` because it uses its own error handler rather than SCSI EH. Don't re-add that
  udev rule — the watchdog is the working substitute.
- **smartd actually alerts now.** It used to be `DEVICESCAN … -m root -M exec …/smartd-runner` with
  **no MTA installed**, so the 2026-07-21 pending-sector warnings went nowhere — that silence is the
  real reason a bad sector became a two-week outage. It now runs `/usr/local/sbin/smart-alert.sh`,
  which logs to `/var/log/smart-alerts.log` + journal (`daemon.crit`) and sends Telegram through the
  hermes bot, reading `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ALLOWED_USERS` from
  `/footage/services/hermes/config/.env` **at run time** — no secret literals on disk or in this repo.
- `lvm2-monitor` is enabled, which is what reports a failed mirror leg.

## LVM traps this migration exposed

1. **Allocated ≠ used.** The old volumes held 805 GiB of data but were **100 % allocated**
   (`VFree 0`), so `pvmove` was impossible — it moves *allocated extents*, not used blocks. A
   filesystem + LV shrink had to come first. Deleting files does **not** reduce `pvmove` work.
2. **`lvreduce` frees the LV's *highest* LEs**, which is not necessarily the disk you want emptied.
   `lvs -o+seg_pe_ranges` showed `libraryLogicalVolume` was laid out `sdb` first, so the shrink freed
   the *`sda`* half. **Always read `seg_pe_ranges` before assuming which disk a shrink will empty.**
3. **`resize2fs` before `lvreduce`, always.** Reversed, it truncates live data. If the box dies
   mid-`resize2fs`: power-cycle, `e2fsck -f`, re-run `resize2fs`, and do not `lvreduce` until it
   reports success.
4. **`lvextend` on a RAID1 LV desyncs the new extents** — `Cpy%Sync` drops back (100 % → 31 % here) and
   a long resync follows. This is **not** a redundancy gap: dm-raid writes go to *both* legs
   immediately, so live data is mirrored as it lands and the resync only reconciles never-written
   regions. Don't stop services over it.
5. **Two LVs syncing at once thrash the heads.** `lvconvert -y -m0 <vg>/<lv> /dev/<new-pv>` detaches
   the unsynced leg — **name the new PV explicitly** so it can never drop the leg holding your data —
   then re-add later with `lvconvert -y --type raid1 -m1`. Losing a few % of sync progress costs
   nothing.
6. **Sync speed is all about contention, not tuning.** Same 1.5 TiB job measured on this box:
   8.5 MB/s (20 containers + an `rm -rf` over many small files) → 37 → 53 → 79 → **154 MB/s with only
   the HA stack up**. Raising `/proc/sys/dev/raid/speed_limit_min` and `lvchange
   --raidminrecoveryrate` changed nothing. Watch for CPU starvation too: Plex post-scan analysis
   (`Plex Transcoder` / `EasyAudioEncoder`) hit 172 % CPU with iowait at 0 % and throttled the sync.

Also: `/footage` is only ~26 G used, and most of it is **Docker's data-root** (`/footage/docker`) —
actual service configs are just ~3.7 G. `services/backup.sh` (root cron, Sundays 05:00) despite its
name backs up **no data**; it is a `git push` of the compose repo.

## History — 2026-08-03 incident (why this rebuild happened)

`smartd` logged pending sectors on both old disks (`sda`: 1, `sdb`: 2) at `Jul 21 16:39:13`, then the
journal went **completely silent for 13 days** — no clean shutdown, no crash dump — until the box was
found unresponsive (ping/ARP dead) on 2026-08-03 and physically power-cycled. A read hit a bad/pending
sector, kernel/LVM I/O hung on it, and the whole box wedged. The host was unreachable at L2 (ARP
`incomplete`), so the only recovery was a physical power cycle. Note that ARP `incomplete` alone does
*not* prove a wedge — on 2026-08-06 the same symptom was just the ethernet being in the other NIC
(`enp3s0` is the live one now). Check the console before assuming the worst. See [[ssh-access]].

The old array was `linear`/concatenated with no redundancy, and `footageLogicalVolume` lived solely on
`sda`, so an `sda` failure would have taken every service config with it. That is what the mirror
fixes.

A first attempt at replacement stalled on 2026-08-06 because the drives bought were **SAS, not SATA**.
This box (ZimaBlade, Apollo Lake) has an AHCI **SATA** controller: SATA drives run on SAS controllers,
never the reverse, and the SAS connector's bridged gap won't seat in a SATA cable. Passive
"SAS→SATA adapters" do **not** bridge the protocol — they adapt connectors for the opposite direction.
A SAS HBA (LSI 9207-8i etc.) would work electrically, but the ZimaBlade's ~36–60 W USB-C PD budget
cannot feed an HBA plus two 3.5" enterprise drives, which also need external power. Only 2 SATA ports
exist (`ata1`/`ata2`), which is why the whole migration had to roll one disk at a time.
