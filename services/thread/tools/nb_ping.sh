L=$1; shift
echo "== $L $(date -u +%FT%TZ) host=$(hostname)"
ip -6 route | grep fde9
for k in "Marked node as unavailable" "Subscription Liveness timeout" "CASESession timed out" "esubscri"; do printf "%s since-7d: " "$k"; sudo journalctl -u matter-server --since -7d | grep -c "$k"; done
for e in "$@"; do IFS== read n name a <<< "$e"
 ( out=$(ping -6 -c 60 -i 1 -W 5 $a 2>&1 | tail -2 | tr '\n' ' '); echo "node $n $name :: $out" ) &
done; wait
