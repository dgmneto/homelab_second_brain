---
name: disk-health-storage-array
description: Both spinning disks in the library/footage LVM array have failing sectors and no redundancy; caused a 13-day silent hang on 2026-08-03
metadata:
  node_type: memory
  type: project
---

# `library` LVM array — failing disks, zero redundancy

The `libraryVirtualGroup` volume group (`vgs`/`pvs`) is built from **two bare spinning disks with no
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

## Open risk — not yet fixed

Pending sectors can grow and the array has no redundancy. Until resolved:
- **Back up `/footage` and anything irreplaceable on `/library` off-box.**
- Consider adding a mirror (second pair of disks + `pvmove`/`lvconvert --type raid1`) or at minimum
  replacing `sdb` (14.6y old, the more concerning of the two) before it fails outright.
- Re-run the `smartctl` check above periodically — a rising pending-sector count means the drive is
  actively degrading, not just old.
