# Counts failed z2m set/get publishes per hour+device since the given time (edit --since). Run with the store python3 (see nm.py).
import json,subprocess,re,collections
out=subprocess.run(["journalctl","-u","zigbee2mqtt","--since","2026-11-24 16:50","-o","cat"],capture_output=True,text=True).stdout
c=collections.Counter()
for l in out.splitlines():
    if "' failed" not in l or "Publish '" not in l: continue
    try: d=json.loads(l)
    except: continue
    m=re.search(r"Publish '(\w+)' '(\w+)' to '([^']+)' failed.*?\((Delivery failed|.*?timed out|[^)]{0,40})",d["message"])
    if m: c[(d["timestamp"][:13], m.group(3), m.group(1), m.group(4)[:30])]+=1
for k,v in sorted(c.items()): print(v,*k)
