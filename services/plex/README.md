# plex

Plex Media Server. Streams the media library with hardware-accelerated
transcoding. Runs on its own dedicated LAN IP via a macvlan network.

## Image

- `plexinc/pms-docker:latest` — **unpinned `:latest`**.

## Access

- LAN IP: **`192.168.14.7`** (macvlan, addressable directly on the network).
- Plex server port: `32400`.
- Public/remote: `https://filmin.3e.dgmneto.com`, proxied by **Nginx Proxy Manager
  `nginxProd`** (proxy host 1) -> upstream `plex:32400`.

## Hardware acceleration / transcoding

- Device passthrough: `/dev/dri:/dev/dri` (Intel/AMD VAAPI iGPU). Host shows
  `card0` and `renderD128`, so HW transcoding is available.
- Enable "Use hardware acceleration when available" in Plex settings to use it
  (requires Plex Pass).
- Transcode cache lives under the config volume
  (`/config/Library/Application Support/Plex Media Server/Cache`).

## Paths

- Compose (server): `/home/dgmneto/homelab/services/plex/compose.yaml`
- Config: `/footage/services/plex/config` -> `/config`
- Media library: `/library/media` -> `/library/media`

## Networks

- `macVlanNetwork` (external macvlan), static `ipv4_address: 192.168.14.7`,
  gateway `192.168.14.1`.
- Because it is macvlan, Plex is reachable on the LAN as its own host but the
  Docker host itself generally cannot talk to it directly (standard macvlan
  limitation).

## Environment

- `.env` keys (values NOT recorded — `PLEX_CLAIM` is a secret token):
  - `PLEX_UID`
  - `PLEX_GID`
  - `UMASK`
  - `TZ`
  - `VERSION`
  - `PLEX_CLAIM` (commented out; one-time claim token — keep secret, never commit)

## Integrations

- `jellyfin` (casaos) shares `/library/media`; its ffmpeg (`/usr/lib/jellyfin-ffmpeg/ffmpeg`) competes for the same weak CPU.
- `hermes` (Orion profile, on homelab-notebook) — read-only API access for playback diagnosis, token-free via `allowedNetworks`; see `ACCESS.md`.
- `overseerr` — request frontend for Plex.
- *arr stack (`radarr`/`sonarr`/`bazarr`) populates `/library/media`.

## Quirks / runbook

### Diagnosing "it keeps buffering" (learned 2026-11-04)
Host CPU is a 4-core **Celeron N3450**, so software 4K transcoding is hopeless. But check what actually happened
before blaming transcoding. Logs: `/footage/services/plex/config/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log`
(sudo on casaos).
1. **Decision:** `grep "Reached Decision id=<ratingKey>"` → `direct play` / `transcode`. Find the ratingKey with `/search?query=`.
2. **Player state:** `grep "timeline?.*ratingKey=<id>"` → `state=buffering|playing`, client IP.
   `/status/sessions` can show **0** while the Apple TV is direct-playing, so trust the log over the API.
3. **Throughput to the client** (bytes per minute of file reads; the part id is in `/library/metadata/<id>` → `Part.id`):
   ```
   sudo grep -h "parts/<partId>" "Plex Media Server.log" | grep Completed \
     | sed -E 's/^... .., .... ([0-9]+:[0-9]+):.* ([0-9]+)ms ([0-9]+) bytes.*/\1 \2 \3/' \
     | awk '{b[$1]+=$3} END{for(k in b) printf "%s %.0f Mbps\n",k,b[k]*8/60e6}' | sort
   ```
   A flat ceiling around 94 Mbps means the client has a **100 Mbps-class link** (Fast Ethernet or weak Wi-Fi).
4. Compare with a LAN box: `curl -o /dev/null -r 0-200000000 -w '%{speed_download}' http://192.168.14.7:32400/library/parts/<partId>/<x>/file.mp4`
   (no token needed from 192.168.0.0/16). homelab-notebook got 150–190 Mbps (2026-11-04).
- **Check the codec tag first for MP4s on the Apple TV:** `docker exec jellyfin /usr/lib/jellyfin-ffmpeg/ffprobe -v error
  -select_streams v:0 -show_entries stream=codec_tag_string -of csv=p=0 "<file>"`. **`hev1` = Apple's player won't start**
  (it spins on "buffering", and the timeline stays at `state=buffering time=0` forever). Plex still says "Direct play OK", because its profile
  doesn't check the tag. Needs `hvc1`/`dvh1`. Fix without re-encoding: `ffmpeg -i in.mp4 -map 0 -c copy -tag:v hvc1 out.mp4`.
  MKVs are not affected. Runbook that worked (2026-11-04, ~14 min for 32 GB at ~40 MB/s): run in the jellyfin container
  (has `/library/media` rw, runs as root) with `docker exec -d jellyfin sh -c 'cd "<dir>" && nice -n 10
  /usr/lib/jellyfin-ffmpeg/ffmpeg -nostdin -y -v warning -progress /config/remux-progress.txt -i "<in>.mp4" -map 0 -c copy
  -tag:v:0 hvc1 -f mp4 remux.hvc1.tmp > /config/remux.log 2>&1; echo EXIT=$? >> /config/remux.log'`
  (`-tag:v:0`, not `-tag:v`: there's also an mjpeg cover "video" stream). Writing to a `.tmp` name stops Plex picking up a partial file.
  The result drops the DV config record (plays as HDR10) and gains one chapter data stream; "codec frame size is not set"
  warnings for EAC3 are harmless. Then `chown` to match, copy the `.pt-BR.srt` under the new basename, and
  `GET /library/sections/2/refresh?path=<urlencoded dir>` (no token from the LAN).
- **Multiple versions:** files in one movie folder whose names start with `Title (Year) - ` show up as versions of one item
  ("Play Version…"). Radarr only tracks one of them; the other is an unmanaged file in the folder.
- **Known case (2026-11-04):** every "Ben The Men" (BTM) WEB-DL MP4 is `hev1`: Spider-Man: Brand New Day + Widow's Bay
  S01 (10 eps, 0 views since July). Spider-Man now has two versions (original `[DV HDR10Plus]` + remuxed `[HDR10 hvc1]`, Plex media 5070). **Confirmed by the user 2026-11-04: the hvc1 version plays on the Apple TV.** The Apple TV link tops out at ~94 Mbps, which is *not* the cause for a 30 Mbps file (an earlier
  analysis blamed it; that was wrong). The re-reads were the player probing, not starvation.

- `restart: unless-stopped`.
- macvlan means no port publishing — connect via `192.168.14.7:32400` or the
  `filmin.3e.dgmneto.com` proxy, not via the host IP.
- If HW transcoding stops working, check `/dev/dri` still passes through and the
  container user is in the `render`/`video` groups.
- NEVER write the Plex claim token or auth tokens into version control.
- The host-side **plex-qbittorrent-watchdog** (paused qBittorrent while Plex streamed) was
  **decommissioned 2026-11-11** — streams and downloads now compete freely. See
  `../plex-qbittorrent-watchdog/README.md`.
