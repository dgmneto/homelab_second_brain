# Unfiltered fabric table per node (which controllers each device is paired with). Run like nodes.py (matter-server env).
# Vendor IDs seen: 4996 Apple Keychain, 4937 Apple Home, 4942 tado, 65521 HA/test.
import asyncio, aiohttp, json
async def main():
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect("ws://127.0.0.1:5580/ws") as ws:
            await ws.receive_json()
            for i, nid in enumerate([2,3,7,8,9,10]):
                await ws.send_json({"message_id": str(i), "command": "read_attribute", "args": {"node_id": nid, "attribute_path": "0/62/1", "fabric_filtered": False}})
                while (m := await ws.receive_json()).get("message_id") != str(i): pass
                r = m.get("result") or m
                v = list(r.values())[0] if isinstance(r, dict) and len(r)==1 else r
                out=[]
                if isinstance(v, list):
                    for f in v: out.append(f'idx{f.get("254")} vendor={f.get("2")} fabric={hex(f.get("3") or 0)} label={f.get("5")!r}')
                else: out=[json.dumps(m)[:300]]
                print("node", nid, " | ".join(out))
asyncio.run(main())
