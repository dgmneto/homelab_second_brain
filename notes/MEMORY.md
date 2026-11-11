- [SSH access](ssh-access.md) — bypass broken 1Password agent with `-o IdentityAgent=none -i ~/.ssh/id_rsa`; server is x86_64 Debian, not a Pi
- [/footage disk leak](footage-disk-leak.md) — recurring outage: chrome.service crash-loop floods /footage, HA looks "down"; `find … -name '*.pma' -delete`
- [qBittorrent mass-stop](qbittorrent-mass-stop.md) — "all downloads paused" usually = watchtower restart, not VPN/disk; diagnose via Chrome WebUI
- [Disk health: casaos storage array](disk-health-storage-array.md) — /footage+/library on LVM RAID1 (new 4TB pair since 2026-08-08); how to check, LVM traps. Old failing disks caused 13-day hang 2026-08-03

Host docs (hardware, access, storage, cron) live in `../hosts/<host>/`; services in `../services/`.
- [LAN IPv6](lan-ipv6.md) — native IPv6 from Zen since 2026-11-01 (/48 2a02:8012:882b::/48, LAN /64 via SLAAC) ; ULA fd00::/64 no longer advertised (2026-11-06); Thread BR = Apple TV .236 (OMR fde9:b6c5:757::/64); inbound = UniFi firewall, External→Internal blocked v4+v6 (config-verified 2026-11-11; casaos has no host fw)
- [UniFi](../services/unifi/README.md) — UDR 192.168.11.1; cloud sessions read it via `UNIFI_API_KEY` + `services/unifi/tools/unifi.sh` (Site Manager connector; local IP blocked by proxy); Tv unit Flex Mini uplink = 100 Mbps (Apple TV cap)
