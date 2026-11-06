#!/usr/bin/env bash
# Read-only drift check for the Thread/Matter firewall rule on homelab-notebook. Run as root.
# Prints WARN lines and exits 1 if the rule's assumptions no longer hold; silent + exit 0 otherwise.
# Not deployed — see ../TADO-X-READINESS.md (prioritised change 1) for how to wire it to a timer.
PREFIX=${PREFIX:-fde9:b6c5:757::/64}   # Thread OMR prefix the firewall rule allows
IFACE=${IFACE:-enp2s0}
MINPORT=${MINPORT:-1024}               # rule's lower dport bound
CHECK_RULE=${CHECK_RULE:-0}            # 1 once the Stage-2 accept rule is deployed
rc=0; warn() { echo "WARN $*"; rc=1; }

# 1. Advertised Thread prefix (RIO from the border router) must equal the firewall's.
adv=$(ip -6 route show dev "$IFACE" proto ra | awk '$2=="via" && $1 ~ /^f[cd]/ {print $1}')
[ -n "$adv" ] || warn "no Thread OMR route on $IFACE (border router down, or prefix withdrawn)"
for p in $adv; do [ "$p" = "$PREFIX" ] || warn "advertised Thread prefix $p != firewall prefix $PREFIX"; done

# 2. matter-server's UDP sockets must fall inside the rule's port range.
#    Use the unit's cgroup: MainPID is the start-script wrapper, the python process is its child.
cg=$(systemctl show -p ControlGroup --value matter-server)
pids=$(cat "/sys/fs/cgroup$cg/cgroup.procs" 2>/dev/null)
[ -n "$pids" ] || warn "matter-server not running"
for pid in $pids; do
  ss -uapnH | grep -F "pid=$pid," | awk '{print $4}' | sed -E 's/.*:([0-9]+)$/\1/'
done | sort -un | while read -r port; do
  [ "$port" = 5353 ] && continue           # mDNS, opened separately
  [ "$port" -ge "$MINPORT" ] || { echo "WARN matter-server UDP port $port < $MINPORT (rule would not match)"; exit 1; }
done || rc=1

# 3. (Stage 2) the accept rule itself must be loaded.
if [ "$CHECK_RULE" = 1 ]; then
  ip6tables -C nixos-fw -i "$IFACE" -s "$PREFIX" -p udp --dport "$MINPORT":65535 -j nixos-fw-accept 2>/dev/null \
    || warn "accept rule for $PREFIX on $IFACE not loaded"
fi
exit $rc
