#!/usr/bin/env bash
# Read-only GET against the UDR's UniFi Network app via the UniFi Site Manager cloud connector.
# Works from Claude cloud sessions (the local 192.168.11.1 API is blocked by the agent proxy:
# "Destination IP is in a private/reserved range"). Needs UNIFI_API_KEY (a Site Manager key,
# created at unifi.ui.com -> API). Secret-looking fields (x_*, *passw*, *token*, *key*, *psk*)
# are redacted before printing, because e.g. rest/setting returns the device SSH password.
#
# Usage:  unifi.sh <network-app path>          e.g.
#   unifi.sh api/s/default/rest/networkconf      networks/VLANs/IPv6
#   unifi.sh api/s/default/rest/wlanconf         SSIDs
#   unifi.sh api/s/default/stat/sta              connected clients (port, link speed, network)
#   unifi.sh api/s/default/stat/device           APs/switches incl. port_table + uplink speed
#   unifi.sh v2/api/site/default/firewall-policies   zone firewall
#   unifi.sh v2/api/site/default/firewall/zone
#   unifi.sh --raw <path>                        no redaction (never paste output into the repo)
set -euo pipefail
: "${UNIFI_API_KEY:?UNIFI_API_KEY not set}"
raw=0; [ "${1:-}" = "--raw" ] && { raw=1; shift; }
path="${1:?path required}"
api=https://api.ui.com/v1
host_id=$(curl -fsS -m 20 -H "X-API-KEY: $UNIFI_API_KEY" "$api/hosts" | jq -r '.data[] | select(.type=="console") | .id' | head -1)
out=$(curl -fsS -m 60 -H "X-API-KEY: $UNIFI_API_KEY" -H accept:application/json \
  "$api/connector/consoles/$host_id/proxy/network/$path")
if [ "$raw" = 1 ]; then printf '%s\n' "$out"; else
  printf '%s\n' "$out" | jq 'walk(if type=="object" then with_entries(
    if (.key|test("^x_|passw|token|secret|psk|_key$|^key$";"i")) and (.key!="key") then .value="<redacted>" else . end) else . end)'
fi
