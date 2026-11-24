#!/bin/zsh
# usage: measure.sh <label>   -> writes <label>.txt
L=$1; OUT=$PWD/$L.txt; : > $OUT
echo "== $L $(date -u +%FT%TZ)" >> $OUT
echo "-- meshcop BRs" >> $OUT
(dns-sd -B _meshcop._udp local. & sleep 4; kill $!) 2>/dev/null | awk 'NR>3' >> $OUT
echo "-- RIO routes" >> $OUT; netstat -rn -f inet6 | grep -i fde9 >> $OUT
while read n h name; do
  a=$(dscacheutil -q host -a name $h.local | awk "/ipv6_address: fde9/{print \$2}" | head -1)
  ( r=$(ping6 -c 30 -i 1 $a 2>&1 | tail -2 | tr '\n' ' '); echo "node $n $name $a :: $r" >> $OUT ) &
done < nodes.txt
wait
cat $OUT
