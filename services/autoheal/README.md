# autoheal — Restart unhealthy containers

Monitors Docker container health status and automatically restarts any
**opted-in** container whose healthcheck reports `unhealthy`. A self-healing
safety net for services that wedge but keep their process alive.

## Image

`willfarrell/autoheal:latest` (container: `autoheal`)

> Pinned to `:latest`. Auto-updated by Watchtower (see `../watchtower`).

## Access

No ports. Runs with `network_mode: none` (no network at all) — it talks only to
the Docker daemon through the mounted socket.

## Compose

Server path: `/home/dgmneto/homelab/services/autoheal/compose.yaml`

No `.env` file. Behaviour is controlled by the image's built-in env defaults:

| Env var | Value | Meaning |
|---|---|---|
| `AUTOHEAL_CONTAINER_LABEL` | `autoheal` | Only watch containers labeled `autoheal=true` (opt-in mode) |
| `AUTOHEAL_INTERVAL` | `5` | Check every 5 seconds |
| `AUTOHEAL_START_PERIOD` | `0` | Grace period (s) before a new container is eligible |
| `AUTOHEAL_DEFAULT_STOP_TIMEOUT` | `10` | Seconds to wait on stop before kill during restart |

Mounts:
- `/var/run/docker.sock:/var/run/docker.sock` — read health, issue restarts.
- `/etc/localtime:/etc/localtime:ro` — correct log timestamps.

## How a container opts in

Because `AUTOHEAL_CONTAINER_LABEL=autoheal` (the image default, **not** `all`),
autoheal restarts a container **only if** it carries:

```yaml
labels:
  autoheal: "true"
```

…and that container has a Docker `HEALTHCHECK` that can go `unhealthy`.

## Networks

`none` — fully network-isolated. Acts purely via the Docker socket.

## Quirks / runbook

- **Currently a no-op.** No container on the host carries the `autoheal=true`
  label, so autoheal is monitoring nothing. Several containers DO report
  `(healthy)` (qbittorrent, prowlarr, gluetun, plex, watchtower) but none have
  opted in. To actually protect a service, add `labels: { autoheal: "true" }`
  to it and ensure it defines a healthcheck.
- To monitor *every* healthcheck-bearing container instead of opting in per
  container, set `AUTOHEAL_CONTAINER_LABEL=all`.
- Mounting `docker.sock` is root-equivalent; `network_mode: none` limits blast
  radius somewhat by removing all network access.
- Restart policy `always`; container reports `(healthy)`.
