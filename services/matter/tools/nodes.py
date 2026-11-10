r"""Dump every Matter node known to matter-server (read-only, websocket get_nodes).

Run from a cloud session (matter-server's ws has no auth, so it must run ON homelab-notebook):
  W=$(ssh claude@homelab-notebook 'sudo cat /proc/$(pgrep -P $(systemctl show -p MainPID --value matter-server))/cmdline | tr "\\0" "\\n" | sed -n 2p')
  ssh claude@homelab-notebook "PY=\$(head -1 $W | cut -c3-); { sed -n 3p $W; cat -; } > /tmp/msenv.py; \$PY /tmp/msenv.py; rm /tmp/msenv.py" < services/matter/tools/nodes.py
Line 3 of matter-server's nix wrapper (`.matter-server-wrapped`) adds its site-packages (aiohttp etc.); the system has
no python3 of its own. Attribute keys are "endpoint/cluster/attribute" (decimal).
"""
import asyncio, aiohttp

def c(v, div=100):
    return None if v is None else v / div

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect("ws://127.0.0.1:5580/ws") as ws:
            info = await ws.receive_json()
            print("sdk", info.get("sdk_version"), "schema", info.get("schema_version"),
                  "thread_credentials_set", info.get("thread_credentials_set"))
            await ws.send_json({"message_id": "1", "command": "get_nodes"})
            while (m := await ws.receive_json()).get("message_id") != "1":
                pass
            for n in sorted(m["result"], key=lambda n: n["node_id"]):
                a = n["attributes"]
                hum = a.get("2/1029/0", a.get("1/1029/0"))
                print(f"node {n['node_id']:>3} avail={n['available']!s:5} {a.get('0/40/1')} {a.get('0/40/3')} "
                      f"sw={a.get('0/40/10')}({a.get('0/40/9')}) hw={a.get('0/40/8')} serial={a.get('0/40/15')} "
                      f"temp={c(a.get('1/513/0'))} heatSP={c(a.get('1/513/18'))} mode={a.get('1/513/28')} "
                      f"hum={c(hum)} batLevel={a.get('0/47/14')} interviewed={n.get('last_interview')}")
asyncio.run(main())
