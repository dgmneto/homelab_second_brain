# shelly (Wi-Fi smart plugs)

Shelly devices on the LAN, integrated into Home Assistant (homelab-notebook) with the built-in `shelly`
integration (local push over the device's WebSocket/RPC; no MQTT, no Shelly cloud needed by HA).

## Devices

| Name | Model | IP / MAC | Wi-Fi | Powers |
|---|---|---|---|---|
| **Bike Charger** | Shelly Plus Plug UK `SNPL-00112UK`, Gen2, fw 1.4.4 (2.0.3 available, not applied) | `192.168.11.252` (DHCP, no reservation) / `C0:CD:D6:4F:00:A4`, hostname `shellypluspluguk-c0cdd64f00a4` | SSID `Amora’s` | e-bike battery charger |

Find a new one: `services/unifi/tools/unifi.sh api/s/default/stat/sta | jq '.data[]|select(.hostname|test("shelly";"i"))|{hostname,ip,mac}'`
(UniFi's `oui` is empty for these, so match the hostname). The local RPC API is open (`auth_en: false`):
`curl http://192.168.11.252/rpc/Shelly.GetStatus` (from homelab-notebook/casaos; cloud sessions can't hit the LAN IP directly, go via `ssh claude@homelab-notebook`).

## Bike Charger: idle safety cut-off (on-device script)

**Script `bike-charger-idle-off` (id 1) runs on the plug itself**, so it works even when HA or Wi-Fi is down.
Source of truth: [bike-charger-idle-off.js](bike-charger-idle-off.js) (keep it identical to the device copy).

- Every 10 s: if the plug is **on** and `apower` ≤ **10 W** continuously for **300 s**, it calls `Switch.Set off`.
  Any reading above 10 W resets the timer; switching on starts a fresh timer.
- **Nothing switches it back on automatically** (`auto_on: false`, no HA automation). Re-enable = the plug's
  physical button, HA (`switch.bike_charger`, dashboard button) or the Shelly app.
- After a power cut the plug comes back **off** (`initial_state: "off"`, the factory default kept on purpose).
- HA exposes the script as `switch.bike_charger_bike_charger_idle_off`: turning it off disables the cut-off.
- Charger idle draw measured 2026-11-26 (on, nothing charging): **0–0.7 W**. Charger rating: **42 V × 3.0 A out (~126 W), 2.5 A @ 240 V in** → ~140 W while charging, so 10 W
  (≈0.2 A at 42 V, the end of the CV taper) separates charging from done with margin. Raised 5 → 10 W on 2026-11-26.
- **Over-power cut:** `switch:0.power_limit` = **700 W** (default 3000; 2.5 A × 240 V = 600 W + margin). Firmware trips the
  plug off on overpower (`binary_sensor.bike_charger_overpowering` in HA).

### Deploy / update the script
From the repo (cloud session), via homelab-notebook:
```
jq -n --rawfile c services/shelly/bike-charger-idle-off.js '{id:1,code:$c,append:false}' > /tmp/put.json
ssh claude@homelab-notebook 'cat > /tmp/put.json; P=http://192.168.11.252/rpc;
  curl -s -X POST -d "{\"id\":1}" $P/Script.Stop; curl -s -X POST -d @/tmp/put.json $P/Script.PutCode;
  curl -s -X POST -d "{\"id\":1}" $P/Script.Start; curl -s "$P/Script.GetStatus?id=1"' < /tmp/put.json
```
(First install was `Script.Create {"name":"bike-charger-idle-off"}` → id 1, then PutCode, `Script.SetConfig {"id":1,"config":{"enable":true}}` = run at boot, Start.)
Code over ~1.5 kB must be sent in chunks (`append: true` for later chunks).
Inspect live state: `curl -s -X POST -d '{"id":1,"code":"lowSince"}' http://192.168.11.252/rpc/Script.Eval`
(returns the uptime in seconds when the current low-power streak began, or `null`).

## Home Assistant

- Integration `shelly`, config entry title "Bike Charger", unique_id `C0CDD64F00A4`, data `{host, port: 80, sleep_period: 0, model, gen: 2}`.
  `shelly` had to be added to `extraComponents` in `hosts/homelab-notebook/nixos/home-automation.nix` (aioshelly was already in the env).
  The entry was **added offline** (no HA token): stop HA, append the entry to `.storage/core.config_entries`, start. Entities appeared on start.
- Entities: `switch.bike_charger`, `sensor.bike_charger_{power,energy,voltage,current,temperature,signal_strength,uptime}`,
  `binary_sensor.bike_charger_{overpowering,overvoltage,overcurrent,overheating,cloud,restart_required}`, `button.bike_charger_restart`,
  `update.bike_charger_firmware`, `switch.bike_charger_bike_charger_idle_off` (the script).
- Dashboard: **Home → Ground Floor → Hall card**, sub-button "Bike Charger" (`mdi:bicycle-electric`, highlighted when on).
  Tap → **more-info dialog** of `switch.bike_charger` (toggle, power/energy). (Was a standalone card for a few minutes on 2026-11-26.)

## Gotchas
- Device and switch-channel names were set to "Bike Charger" via RPC before adding to HA: HA derives entity IDs from them.
  Renaming in the Shelly app later does not rename HA entity IDs.
- Shelly cloud is enabled (`cloud.connected: true`): that's what the Shelly app uses off-LAN. HA doesn't need it.
