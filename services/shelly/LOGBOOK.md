# Logbook — shelly

Reverse-chronological. Newest entry on top. See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-26 — Bike Charger plug set up (script + HA)
Found `shellypluspluguk-c0cdd64f00a4` at 192.168.11.252 via `unifi.sh api/s/default/stat/sta` (fw 1.4.4, auth off, no scripts).
RPC from homelab-notebook: set device + switch:0 name "Bike Charger"; `Script.Create` → id 1, `PutCode`
(bike-charger-idle-off.js), `SetConfig enable:true`, `Start`. Live test with the charger idle at 0–0.7 W: off at uptime 990 s
(streak began at 680 s). The first streak (started ~450 s) reset once at ~670 s for an unknown reason, possibly a brief
>5 W blip; if the cut-off seems late, log `apower` + `lowSince` as in the README. Plug left **off**. Firmware 2.0.3 not applied.
