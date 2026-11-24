# Logbook — thread

Reverse-chronological. Newest entry on top. One entry per task that touches the **Thread** network / border routers.
See `../../LOGBOOK.md` for the project-wide log.

## 2026-11-24 — HA OTBR integration added for the SLZB-MR5U
At the user's request: HA UI, add `otbr` with URL `http://192.168.11.121:8080` → "Created configuration". OTBR unchanged after
(`MyHome1662126353`, rloc 0xe000, router, same partition). HA Thread panel: preferred `MyHome1662126353`, 2 BRs (Living Room + SLZB-MR5U).
SMLIGHT discovery for the MR5U left un-added.

## 2026-11-24 — SLZB-MR5U added as 2nd Thread border router (joined Apple network)
Found the new SLZB-MR5U at `192.168.11.121` (mDNS `_slzb-06._tcp`), SLZB-OS v3.2.6.dev3, 2× EFR32MG24 both on Zigbee fw.
Baseline first (Mac + wired homelab-notebook pings to the 6 tado nodes, matter-server 7-day counts). Web UI Mode → **Radio 2 →
"Thread+OTBR running on device"** (needed `window.confirm=()=>true`; flashed RCP fw 20251218). OTBR immediately formed its own
`OpenThread-ESP` network as leader → `PUT /node/state "disable"`, pushed HA's preferred (Apple, iOS-synced) dataset with
`tools/push_dataset.py` (name check `MyHome1662126353`, TLV never printed), `"enable"` → child 30 s → router 0xe000 at ~2 min, LQ 3/3
to the Apple TV. `_meshcop` now lists 2 BRs; homelab-notebook got an ECMP OMR route via both. Reboot test: back as router in ~10 s,
dataset persisted; 10/150 ping loss during the reboot. After-measurement within noise (all children still on the Apple TV); Office
TRV loss 13.3 % → 1.7 %. Radio 1 (Zigbee) untouched. HA `otbr` integration not added. Details + table: README.
