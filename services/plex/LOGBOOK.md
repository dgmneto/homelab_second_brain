# Logbook — plex

Reverse-chronological. Newest entry on top. One entry per task that touches **plex** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-04 — Spider-Man: added hvc1 remux as a second version
Remuxed copy (`[HDR10 hvc1]`, media 5070) next to the original (media 4960); both under ratingKey 4219. Runbook in README.
Pending Apple TV confirmation.

## 2026-11-04 — Spider-Man buffering root cause: `hev1` tag (corrects the entry below)
ffprobe: video codec_tag `hev1`, DV p8.1. Apple TV never left `buffering time=0`. 11 BTM MP4s affected (Spider-Man,
Widow's Bay S01). Network (~94 Mbps) was a red herring. README runbook updated. Remux pending the user's OK.

## 2026-11-04 — Investigation: Spider-Man buffering (Apple TV)
Direct play confirmed in the log; the client link is capped at ~94 Mbps and AVPlayer re-fetched 49 % of the bytes, so the
effective rate ≈ the 30 Mbps bitrate. Added a "Diagnosing buffering" runbook to README. No Plex change.

## 2026-11-04 — Documented token-free LAN API access (for Hermes/Orion)
Read-only check: Preferences `allowedNetworks=192.168.0.0/16`, so homelab-notebook gets 200 on
`/status/sessions`, `/transcode/sessions`, `/library/sections` without a token. No Plex change. ACCESS.md updated.

## 2026-09-22 — Investigation: reported down, found up
Plex up 7d healthy; `/identity` 200 direct, via `filmin.3e` on LAN, and from the internet. Streamed
at 20:24. `filmin.intern.dgmneto.com` broken (no nginxIntern proxy host, TLS unrecognized name) but is
listed in Plex `customConnections`. Remote Access NAT-PMP fails ("Not Supported by gateway"),
state `Mapped - Not Published`, so remote clients rely on the `filmin.3e` custom URL.

## 2026-06-09 — Hello World
Logbook initiated alongside `README.md`. Documented from live server state; no change made to the running service.
