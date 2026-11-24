# pihole

Ad-blocking DNS server for the **whole tailnet** (and the LAN, if a device points at it). Runs on
[homelab-notebook](../../hosts/homelab-notebook/README.md) as native NixOS modules
(`services.pihole-ftl` + `services.pihole-web`), declared in
[`hosts/homelab-notebook/nixos/pihole.nix`](../../hosts/homelab-notebook/nixos/pihole.nix). Installed 2026-10-28
(pihole 6.4.2, FTL 6.7.1, web 6.6, from nixpkgs 26.05).

| | |
|---|---|
| DNS | `100.67.47.127:53` (tailnet), `192.168.11.21:53` (LAN), TCP+UDP |
| Web UI | `http://100.67.47.127/admin/` (or `http://192.168.11.21/admin/`, `http://pi.hole/admin/` when using it as DNS). Plain HTTP on port 80 (tailnet is WireGuard-encrypted anyway) |
| Upstreams | `1.1.1.1`, `1.0.0.1`, `9.9.9.9`; DNSSEC on |
| Blocklist | StevenBlack unified hosts (~76k domains). Refreshed weekly by `pihole-gravity.timer` (Sun ~04:17) |
| Listening mode | `ALL` — required, tailnet clients (100.64/10) are not a "local" subnet so the default `LOCAL` refuses them. The NixOS firewall is the guard (53 + 80 open) |
| Query logs | kept 90 days (`queryLogDeleter`) |
| State | `/var/lib/pihole` (gravity.db, FTL db), config `/etc/pihole/pihole.toml` (generated, read-only) |

## Web UI password
Not in the nix store or this repo. `FTLCONF_webserver_api_password=<pw>` lives in **`/etc/pihole-secrets.env`**
(root 0600, generated randomly on the box 2026-10-28), loaded via `EnvironmentFile=` on `pihole-ftl`. If
the file is missing the UI has **no password**. To get it into 1Password (from the Mac):
```
ssh homelab-notebook 'sudo cat /etc/pihole-secrets.env' | cut -d= -f2- | \
  xargs -I{} op item create --vault Homelab --category login --title "Pi-hole" \
  --url http://100.67.47.127/admin/ 'password={}'
```
To change it: edit the file, `sudo systemctl restart pihole-ftl`.
Settings are **read-only** from the UI (`misc.readOnly`, module default) — change them in `pihole.nix`
and redeploy. Allow/deny-listing individual domains in the UI still works (that's gravity.db, not toml).

## Phones / any device on every network (Tailscale DNS)
Done in the **Tailscale admin console → DNS** (one-time, tailnet-wide):
1. *Nameservers → Global nameservers → Add nameserver → Custom* → `100.67.47.127`.
2. Enable **Override DNS servers** (aka "Override local DNS") so devices use it instead of whatever
   Wi-Fi/cellular hands out.
3. Keep MagicDNS on (ts.net names still work; 100.100.100.100 forwards everything else to Pi-hole).

On the phone: Tailscale app connected, and **Use Tailscale DNS settings** on (default). iOS: in the
Tailscale app enable *VPN On Demand* / keep it connected; Android: set Tailscale as *Always-on VPN*, and
Private DNS = *Off* or *Automatic* (a named Private DNS provider bypasses Pi-hole).

Servers deliberately opt out: casaos and homelab-notebook run `--accept-dns=false`, so they keep the router's
DNS and Pi-hole can't loop to itself or take the homelab down with it.

**Trade-off:** with only Pi-hole as global nameserver, if homelab-notebook is down, tailnet devices lose DNS
while Tailscale is connected (disconnect Tailscale to recover). Adding a public resolver as a second
global nameserver gives fallback but lets some queries skip the blocking.

## Troubleshooting "Pi-hole isn't working" (start here)
Almost always the server is fine and **clients aren't sending it queries**. Check in this order:
1. **Is the tailnet still pointing at it?** `tailscale dns status` on any node with accept-dns on (a cloud
   session works). Under *Resolvers* it must list `100.67.47.127`. If it says *"no resolvers configured"*,
   the global nameserver was removed in the admin console → re-add it (section below). This was the cause on
   2026-11-24.
2. **Who is actually querying?** On the box, with `F=$(systemctl show -p ExecStart pihole-ftl | grep -o '/nix/store/[^ ;]*pihole-FTL' | head -1)`:
   `sudo $F sqlite3 /var/lib/pihole/pihole-FTL.db "select client, datetime(max(timestamp),'unixepoch') from queries group by client order by 2 desc;"`
   A client whose last query is days old has stopped using Pi-hole.
3. **Is it blocking?** Test *on the box* (no `dig` installed: `nix shell nixpkgs#dnsutils -c dig +short @127.0.0.1 doubleclick.net` → `0.0.0.0`).
   `sudo grep -a 'gravity blocked' /var/log/pihole/pihole.log | tail` shows live blocks (`-a`: the log has binary bytes).

## Gotchas
- **Don't test DNS from a Claude cloud session.** UDP/53 from the cloud container to `100.67.47.127` is
  answered by something in the sandbox, *not* Pi-hole — the query never reaches the box (absent from its log)
  and `doubleclick.net` comes back with real Google IPs, `pi.hole` with NXDOMAIN. Run `dig` on homelab-notebook
  or casaos instead.
- **`pihole status` lies**: it prints "DNS service is NOT running" (plus a `FTL_PID_FILE: readonly variable`
  error) even when `pihole-ftl` is up and answering. Use `systemctl status pihole-ftl`. `pihole -q <domain>` works.
- `pihole-FTL` and `sqlite3` aren't on `PATH`; use the nix-store path of `pihole-FTL` (`pihole-FTL sqlite3 ...`,
  `pihole-FTL --config dns.blocking.active`). In SQL use single quotes for strings.
- **Re-running `pihole-ftl-setup.service` fails** (`database_error`) — it re-adds the already-present list.
  It's a one-shot at boot; gravity still gets built. Don't use it to refresh lists — use
  `sudo systemctl start pihole-gravity` (or `sudo -u pihole pihole -g`).

## Checks
```
dig +short @100.67.47.127 doubleclick.net   # 0.0.0.0 = blocked
dig +short @100.67.47.127 example.com       # real IPs
systemctl status pihole-ftl; systemctl list-timers pihole-gravity
```
