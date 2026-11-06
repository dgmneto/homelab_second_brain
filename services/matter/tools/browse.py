import sys, time
for p in sys.argv[1:]: sys.path.insert(0, p)
from zeroconf import Zeroconf, ServiceBrowser, IPVersion, InterfaceChoice
types = ["_meshcop._udp.local.", "_trel._udp.local.", "_srpl-tls._tcp.local.", "_matter._tcp.local.",
         "_matterc._udp.local.", "_matterd._udp.local.", "_airplay._tcp.local.", "_hap._udp.local.", "_hap._tcp.local."]
REDACT = {b"xp", b"at", b"pt", b"pc", b"id", b"psk", b"pskc"}
zc = Zeroconf(interfaces=["192.168.11.21", "fe80::ace7:3469:c9c6:1729%2"] , ip_version=IPVersion.All)
found = {}
class L:
    def add_service(s, zc, t, n): found.setdefault(t, set()).add(n)
    update_service = add_service
    def remove_service(s, zc, t, n): pass
bs = [ServiceBrowser(zc, t, L()) for t in types]
time.sleep(8)
for t in types:
    names = sorted(found.get(t, []))
    print(f"== {t} ({len(names)})")
    for n in names:
        i = zc.get_service_info(t, n, timeout=3000)
        if not i: print("  ", n, "(no info)"); continue
        props = {k.decode(errors='replace'): ("<redacted>" if k in REDACT else (v.hex() if k in (b"sb", b"xa", b"omr") and v else (v.decode(errors='replace') if v else v))) for k, v in i.properties.items()}
        if t.startswith("_airplay") or t.startswith("_hap"):
            props = {k: v for k, v in props.items() if k in ("model", "md", "ci", "srcvers", "osvers", "deviceid")}
        print("  ", n, "|", i.server, "|", [str(a) for a in i.ip_addresses_by_version(IPVersion.All)], "| port", i.port, "|", props)
zc.close()
