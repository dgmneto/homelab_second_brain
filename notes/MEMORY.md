- [SSH access](ssh-access.md) — bypass broken 1Password agent with `-o IdentityAgent=none -i ~/.ssh/id_rsa`; server is x86_64 Debian, not a Pi
- [/footage disk leak](footage-disk-leak.md) — recurring outage: chrome.service crash-loop floods /footage, HA looks "down"; `find … -name '*.pma' -delete`
- [qBittorrent mass-stop](qbittorrent-mass-stop.md) — "all downloads paused" usually = watchtower restart, not VPN/disk; diagnose via Chrome WebUI
- [Disk health: casaos storage array](disk-health-storage-array.md) — /footage+/library on LVM RAID1 (new 4TB pair since 2026-08-08); how to check, LVM traps. Old failing disks caused 13-day hang 2026-08-03

Host docs (hardware, access, storage, cron) live in `../hosts/<host>/`; services in `../services/`.
