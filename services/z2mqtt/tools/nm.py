import json,subprocess,re,sys
# Box has no python3 on PATH: run as  sudo /nix/store/*-python3-3.12*/bin/python3 nm.py  (latest network map from the journal: parents/children)
out=subprocess.run(["journalctl","-u","zigbee2mqtt","--since","-30h","-o","cat"],capture_output=True,text=True).stdout
last=None
for l in out.splitlines():
    if "bridge/response/networkmap" in l:
        try: last=(json.loads(l)["timestamp"], l)
        except: pass
ts,l=last
m=json.loads(l)["message"]; p=json.loads(m[m.index("payload '")+9:-1])
v=p["data"]["value"]; print("map at",ts)
nodes={n["ieeeAddr"]:n for n in v["nodes"]}
for n in v["nodes"]: print(n["type"][:6], n["networkAddress"], n.get("friendlyName"), "lastseen", n.get("lastSeen"))
print("links (source -> target lqi rel):")
for k in v["links"]:
    s=nodes.get(k["source"]["ieeeAddr"],{}).get("friendlyName"); t=nodes.get(k["target"]["ieeeAddr"],{}).get("friendlyName")
    print(f'  {s} -> {t} lqi={k["lqi"]} rel={k.get("relationship")} depth={k.get("depth")}')
