import json, sys, urllib.request
d=json.load(open("/var/lib/hass/.storage/thread.datasets"))["data"]
ds=[v for v in d["datasets"] if v["id"]==d["preferred_dataset"]][0]
b=bytes.fromhex(ds["tlv"]); i=0; info={}
while i < len(b):
    t,l=b[i],b[i+1]; v=b[i+2:i+2+l]; i+=2+l
    if t==0: info["channel"]=int.from_bytes(v[1:],"big")
    if t==1: info["panid"]=hex(int.from_bytes(v,"big"))
    if t==3: info["name"]=v.decode()
    if t==7: info["mesh_local_prefix"]=v.hex()
print("preferred dataset:", info)
if len(sys.argv)>1 and sys.argv[1]=="push":
    if info.get("name")!="MyHome1662126353": sys.exit("name mismatch, abort")
    r=urllib.request.Request("http://192.168.11.121:8080/node/dataset/active", data=ds["tlv"].encode(), method="PUT", headers={"Content-Type":"text/plain"})
    print("PUT active dataset ->", urllib.request.urlopen(r, timeout=10).status)
