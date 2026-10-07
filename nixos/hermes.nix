# Hermes Agent (NousResearch), native systemd service.
# Migrated from Docker on casaos (192.168.11.13); see ~/homelab services/hermes.
{ pkgs, lib, ... }:

let
  # nixos-26.05 ships SQLite 3.51.2, which has the WAL-reset corruption bug
  # (https://sqlite.org/wal.html#walresetbug); Hermes needs >= 3.51.3. Because
  # hermes-agent follows system nixpkgs (RAM limit), its Python links 3.51.2.
  # Rebuilding Python is too heavy for this box, so build only SQLite and put
  # it first on the Hermes units' library path (LD_LIBRARY_PATH beats RUNPATH).
  # Drop this once 26.05 backports the fix or the follows is removed.
  sqliteFixed = pkgs.sqlite.overrideAttrs (_: {
    doCheck = false; # full fuzz suite takes ages on this CPU
    version = "3.53.3";
    src = pkgs.fetchurl {
      url = "https://sqlite.org/2026/sqlite-src-3530300.zip";
      hash = "sha256-u4C/ijv/wZJBzoq6WkvHTpw5gAE8sLXw8JdqmVFpQq8=";
    };
  });
  hermesEnv = { LD_LIBRARY_PATH = "${lib.getLib sqliteFixed}/lib"; };
in
{
  services.hermes-agent = {
    enable = true;
    # stateDir = /var/lib/hermes; HERMES_HOME = /var/lib/hermes/.hermes
    addToSystemPackages = true;

    # Secrets (OPENROUTER_API_KEY, TELEGRAM_*, HERMES_DASHBOARD_BASIC_AUTH_*,
    # API_SERVER_KEY). Plain 0600 file, not in git. TODO: move to sops-nix.
    environmentFiles = [ "/var/lib/hermes/env" ];

    # Only the keys we want pinned; everything else in config.yaml is
    # agent-managed on disk and survives rebuilds.
    settings = {
      model = {
        provider = "openrouter";
        default = "qwen/qwen3.8-max";
      };
      # NPM (nginxIntern on casaos) proxies hermes.intern.dgmneto.com here;
      # public_url makes the dashboard accept that Host header.
      dashboard.public_url = "https://hermes.intern.dgmneto.com";
    };

    backend = {
      mode = "dashboard";
      host = "0.0.0.0"; # access restricted by firewall below
      port = 9119;
    };

    extraPackages = with pkgs; [
      himalaya # email CLI (was /opt/data/bin/himalaya)
      chromium # browser tool
      curl
      jq
      python3
    ];
  };

  # Same limits the container had.
  systemd.services.hermes-agent.serviceConfig = {
    MemoryMax = "2G";
    CPUQuota = "100%";
    TasksMax = 256;
    # Gateway drains for up to restart_drain_timeout (180s) + cron (30s).
    TimeoutStopSec = 240;
  };
  systemd.services.hermes-agent.environment = hermesEnv;
  systemd.services.hermes-backend.environment = hermesEnv;

  # Dashboard: only reachable from NPM (nginxIntern) on casaos. It can come
  # from its macvlan IP or the host IP depending on route.
  networking.firewall.extraCommands = ''
    iptables -I nixos-fw -p tcp --dport 9119 -s 192.168.14.34 -j nixos-fw-accept
    iptables -I nixos-fw -p tcp --dport 9119 -s 192.168.11.13 -j nixos-fw-accept
  '';
  networking.firewall.extraStopCommands = ''
    iptables -D nixos-fw -p tcp --dport 9119 -s 192.168.14.34 -j nixos-fw-accept || true
    iptables -D nixos-fw -p tcp --dport 9119 -s 192.168.11.13 -j nixos-fw-accept || true
  '';
}
