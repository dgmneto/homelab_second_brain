# watchtower — Automatic container image updater

Watches running containers and automatically pulls newer images, recreating
containers when their `:latest` tag moves. Keeps the whole homelab current
without manual `docker pull` / `up`.

## Image

`containrrr/watchtower:latest` (container: `watchtower`)

> Self-updates as well, since it watches all containers (see scope below).

## Access

No published ports for normal use. (The image's internal metrics/health port
`8080/tcp` is exposed by the image but not mapped to the host.)

## Compose

Server path: `/home/dgmneto/homelab/services/watchtower/compose.yaml`

No `.env` file — fully configured via the `command` flags below.

```
command: --interval 30 --cleanup
```

Mounts `/var/run/docker.sock:/var/run/docker.sock` so it can inspect and
recreate containers.

## Schedule & scope

- **Interval: `--interval 30` = every 30 seconds.** This is very aggressive
  (the more common config is a daily cron). Every 30s Watchtower checks all
  watched containers for newer images.
- **Scope: ALL containers.** There is no scope/label filter on the command and
  no `WATCHTOWER_LABEL_ENABLE`. Watchtower defaults to watching **every**
  container on the host (currently all ~18: plex, sonarr, radarr, the two NPMs,
  home assistant, qbittorrent, gluetun, etc.), not an opt-in subset.
- **Cleanup: `--cleanup`** — old images are removed after a successful update.

### How a container opts out

Since the default is "watch everything", to *exclude* a container set a label
on that container:

```yaml
labels:
  com.centurylinklabs.watchtower.enable: "false"
```

(No container currently sets this label, so nothing is excluded.)

## Networks

None declared — runs on its own default bridge (`watchtower_default`). Reaches
the Docker daemon via the mounted socket, and registries via outbound internet.

## Quirks / runbook

- **30-second interval is a surprise.** It means images are pulled almost
  immediately on publish across the entire stack, including pinned `:latest`
  infra (both NPMs, gluetun VPN, etc.). Unattended `:latest` updates can break
  services on a bad upstream release. Consider widening the interval or switching
  to label-enable scope if updates ever cause churn.
- Mounting `docker.sock` grants Watchtower full control of the Docker daemon —
  treat it as root-equivalent.
- Restart policy `always`; container reports `(healthy)`.
