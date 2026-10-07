# Hermes Agent (NousResearch), native systemd service.
# Migrated from Docker on casaos (192.168.11.13); see ~/homelab services/hermes.
{ pkgs, ... }:

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
  };

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
