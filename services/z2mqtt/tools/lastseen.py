import json, time, sys
since = float(sys.argv[1]) if len(sys.argv) > 1 else 0
now = time.time()
rows = []
for line in open("/var/lib/zigbee2mqtt/database.db"):
    d = json.loads(line)
    if d.get("type") == "Coordinator":
        print("coordinator", d.get("ieeeAddr")); continue
    ls = (d.get("lastSeen") or 0) / 1000
    rows.append((ls, d.get("ieeeAddr"), d.get("type"), d.get("modelId")))
names = {}
try:
    import re
    cur = None
    for l in open("/var/lib/zigbee2mqtt/devices.yaml"):
        m = re.match(r"^'?(0x[0-9a-f]{16})'?:", l)
        if m: cur = m.group(1)
        m = re.match(r"^\s+friendly_name:\s*'?(.*?)'?\s*$", l)
        if m and cur: names[cur] = m.group(1)
except Exception: pass
for ls, ieee, typ, model in sorted(rows):
    flag = "OK " if ls >= since else "-- "
    print(flag, time.strftime("%H:%M:%S", time.localtime(ls)) if ls else "never   ", f"{int(now-ls):>6}s ago", typ, names.get(ieee, ieee))
