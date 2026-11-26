// Bike charger safety cut-off, runs ON the Shelly Plus Plug UK (192.168.11.252).
// If the plug is ON and draws <= THRESHOLD_W continuously for IDLE_S seconds, switch it OFF.
// Nothing turns it back on automatically (auto_on=false): re-enable with the plug's button,
// Home Assistant or the Shelly app. The idle timer restarts every time the plug is switched on.
// Deployed via services/shelly/README.md ("Deploy the script"); keep this file = the device copy.

let THRESHOLD_W = 5;   // charger draw at/below this counts as "idle/finished"
let IDLE_S = 300;      // 5 minutes
let POLL_S = 10;

let lowSince = null;   // uptime (s) when the low-power streak began

Timer.set(POLL_S * 1000, true, function () {
  let sw = Shelly.getComponentStatus("switch", 0);
  let now = Shelly.getComponentStatus("sys").uptime;
  if (!sw.output || sw.apower > THRESHOLD_W) {
    lowSince = null;
    return;
  }
  if (lowSince === null) {
    lowSince = now;
    return;
  }
  if (now - lowSince >= IDLE_S) {
    print("idle " + JSON.stringify(sw.apower) + "W for " + JSON.stringify(now - lowSince) + "s -> off");
    lowSince = null;
    Shelly.call("Switch.Set", { id: 0, on: false });
  }
});
