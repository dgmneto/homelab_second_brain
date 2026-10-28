{ config, lib, ... }:

# Pi-hole (FTL + web UI) as the tailnet's ad-blocking DNS server.
# Phones use it from any network via Tailscale admin console -> DNS ->
# global nameserver 100.67.47.127 + "Override DNS servers" (services/pihole/README.md).
{
  services.pihole-ftl = {
    enable = true;
    openFirewallDNS = true;
    openFirewallWebserver = true;
    queryLogDeleter.enable = true;
    lists = [
      {
        url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts";
        description = "Steven Black's unified adlist";
      }
    ];
    settings = {
      dns = {
        # Answer tailnet clients (100.64.0.0/10 isn't a "local" subnet, so the
        # default LOCAL mode would refuse them). The NixOS firewall guards 53.
        listeningMode = "ALL";
        upstreams = [ "1.1.1.1" "1.0.0.1" "9.9.9.9" ];
        dnssec = true;
      };
      # Gravity updates (pihole -g) run from the web API; keep them on.
      webserver.api.cli_pw = true;
    };
  };

  services.pihole-web = {
    enable = true;
    # Plain HTTP: tailnet traffic is already WireGuard-encrypted.
    ports = [ "80" ];
  };

  # Web UI password is not in the store: FTLCONF_webserver_api_password=... lives in
  # this root-only file (generated on the box). Missing file -> UI has no password.
  systemd.services.pihole-ftl.serviceConfig.EnvironmentFile = "-/etc/pihole-secrets.env";

  # The module only runs gravity at setup (and re-running pihole-ftl-setup fails on
  # the already-added list), so refresh the blocklists weekly ourselves.
  systemd.services.pihole-gravity = {
    description = "Pi-hole gravity (blocklist) update";
    after = [ "pihole-ftl.service" "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      User = "pihole";
      Group = "pihole";
      ExecStart = "${lib.getExe config.services.pihole-ftl.piholePackage} -g";
    };
  };
  systemd.timers.pihole-gravity = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "Sun 04:17";
      Persistent = true;
      RandomizedDelaySec = "30m";
    };
  };
}
