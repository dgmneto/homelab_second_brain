#!/bin/bash
# Cloud sessions only: join the tailnet with $TS_AUTHKEY and make `ssh casaos` work.
# Recipe + gotchas: services/tailscale/README.md ("Claude cloud sessions").
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

TS_DIR=/opt/tailscale
SOCK=/var/run/tailscale/tailscaled.sock  # default path; a long --socket path fails with "bind: invalid argument"

# Binaries + ssh client (cached in the container snapshot after the first run)
if [ ! -x "$TS_DIR/tailscaled" ]; then
  mkdir -p "$TS_DIR"
  curl -fsSL https://pkgs.tailscale.com/stable/tailscale_latest_amd64.tgz | tar xz -C "$TS_DIR" --strip-components=1
  ln -sf "$TS_DIR/tailscale" /usr/local/bin/tailscale
  ln -sf "$TS_DIR/tailscaled" /usr/local/bin/tailscaled
fi
if ! command -v ssh >/dev/null; then
  (apt-get install -y -qq openssh-client || (apt-get update -qq && apt-get install -y -qq openssh-client)) >/dev/null
fi

# ssh config: tailscaled runs in userspace mode, so tunnel through `tailscale nc`
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat > ~/.ssh/config <<'CFG'
Host casaos homelab
  HostName casaos
  User claude  # passwordless sudo; tailnet ssh rule only allows this user
  ProxyCommand tailscale nc casaos %p
Host homelab-notebook
  HostName homelab-notebook
  User claude  # passwordless sudo; Tailscale SSH, same tailnet rule as casaos
  ProxyCommand tailscale nc homelab-notebook %p
Host *
  StrictHostKeyChecking accept-new
CFG
chmod 600 ~/.ssh/config

if [ -z "${TS_AUTHKEY:-}" ]; then
  echo "session-start: TS_AUTHKEY not set; skipping tailnet join" >&2
  exit 0
fi

# Daemon: state=mem: makes the node ephemeral, so sessions don't pile up stale devices
if ! tailscale status >/dev/null 2>&1; then
  if ! pgrep -x tailscaled >/dev/null; then
    mkdir -p "$(dirname "$SOCK")"
    setsid nohup tailscaled --tun=userspace-networking --socks5-server=localhost:1055 \
      --state=mem: --socket="$SOCK" >/var/log/tailscaled.log 2>&1 < /dev/null &
    for _ in $(seq 20); do [ -S "$SOCK" ] && break; sleep 0.5; done
  fi
  tailscale up --auth-key="$TS_AUTHKEY" --hostname=claude-cloud-session --accept-routes --timeout=60s >/dev/null
fi

echo "session-start: tailnet up as $(tailscale ip -4 2>/dev/null | head -1)" >&2
