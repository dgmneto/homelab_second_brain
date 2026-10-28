# hosts/

One folder per physical machine: hardware, OS, access (SSH), storage, host-level cron/timers, and
host-level logbook. **What runs on a host** is documented per service under [../services/](../services/);
each service's README says which host it lives on, and [../services/README.md](../services/README.md)
has the service → host map.

| Host | IP | OS / runtime | SSH | Runs |
|---|---|---|---|---|
| [casaos](casaos/README.md) | `192.168.11.13` | x86_64 Debian 12, Docker compose | `ssh dgmneto@homelab` (fallback key `~/.ssh/id_rsa`) | every service except hermes |
| [homelab-notebook](homelab-notebook/README.md) | `192.168.11.21` (DHCP) | NixOS 26.05, native modules, no Docker | `ssh homelab-notebook` (key only in 1Password) | hermes |

Adding a host: create `hosts/<hostname>/README.md` (hardware, OS, access, storage, deploy method) +
`LOGBOOK.md`, add a row above, and add it to the hosts table in `../CLAUDE.md`.
