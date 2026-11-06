import socket, struct, time, ipaddress
IF = "enp2s0"; idx = socket.if_nametoindex(IF)
s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, IF.encode())
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, idx)
s.sendto(bytes([133, 0, 0, 0, 0, 0, 0, 0]), ("ff02::2", 0, 0, idx))  # Router Solicitation
s.settimeout(1); end = time.time() + 12; seen = set()
while time.time() < end:
    try: d, a = s.recvfrom(4096)
    except socket.timeout: continue
    if d[0] != 134: continue
    key = (a[0], d[8:]);
    if key in seen: continue
    seen.add(key)
    lt = struct.unpack("!H", d[6:8])[0]; flags = d[5]
    print(f"RA from {a[0]}  router_lifetime={lt}s  M={flags>>7&1} O={flags>>6&1} prf={(flags>>3)&3}")
    o = 16
    while o + 2 <= len(d):
        t, l = d[o], d[o+1]*8
        if l == 0: break
        b = d[o:o+l]
        if t == 3:
            pl, fl = b[2], b[3]; vl, pf = struct.unpack("!II", b[4:12])
            print(f"   PIO {ipaddress.IPv6Address(b[16:32])}/{pl} L={fl>>7&1} A={fl>>6&1} valid={vl} pref={pf}")
        elif t == 24:
            pl = b[2]; prf = (b[3]>>3)&3; lt2 = struct.unpack("!I", b[4:8])[0]
            p = b[8:] + bytes(16 - len(b[8:]))
            print(f"   RIO {ipaddress.IPv6Address(p)}/{pl} prf={prf} lifetime={lt2}")
        elif t == 25: print(f"   RDNSS {[str(ipaddress.IPv6Address(b[8+i:24+i])) for i in range(0, l-8, 16)]}")
        elif t == 38:
            sl = struct.unpack("!H", b[2:4])[0]; plc = sl & 7; lens = {0:96,1:64,2:56,3:48,4:40,5:32}
            print(f"   PREF64 {ipaddress.IPv6Address(b[4:16]+bytes(4))}/{lens.get(plc)} lifetime={sl & 0xfff8}s")
        elif t == 5: print(f"   MTU {struct.unpack('!I', b[4:8])[0]}")
        elif t == 1: pass
        else: print(f"   opt type {t} len {l}")
        o += l
