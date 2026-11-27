#!/bin/sh
# usage: zq.sh <topic-suffix> <payload>   (publishes to zigbee2mqtt/<suffix>)
M=$(ls -d /nix/store/*-mosquitto-2.1.2/bin | head -1)
P=$(sed -n 's/^mqtt_password: *//p' /var/lib/zigbee2mqtt/secret.yaml | tr -d "'\"")
$M/mosquitto_pub -h 127.0.0.1 -u zigbee2mqtt -P "$P" -t "zigbee2mqtt/$1" -m "$2"
