{ config, lib, pkgs, pkgsUnstable, ... }:

# Home-automation stack, migrating from casaos Docker in phases
# (plan + runbook: services/homeassistant/MIGRATION.md). Each service stays off until
# its phase; flip one toggle, deploy, cut over. The `homelab-notebook-ha-preview`
# flake output builds with everything on, to warm the store without switching.
let
  cfg = config.homelab.homeAutomation;
  casaos = {
    mosquitto = "192.168.14.82";
  };
in
{
  options.homelab.homeAutomation = {
    mosquitto.enable = lib.mkEnableOption "Mosquitto broker (phase 1)";
    zigbee2mqtt.enable = lib.mkEnableOption "zigbee2mqtt (phase 2)";
    matter.enable = lib.mkEnableOption "python-matter-server (phase 3)";
    homeAssistant.enable = lib.mkEnableOption "Home Assistant (phase 4)";
  };

  config = lib.mkMerge [
    {
      # HA and z2m address the broker by its old Docker DNS name. Map it here so the
      # phase-1 cutover is a hosts change, not an edit of both apps' configs.
      networking.hosts.${if cfg.mosquitto.enable then "127.0.0.1" else casaos.mosquitto} = [ "mosquitto" ];
    }

    (lib.mkIf cfg.mosquitto.enable {
      # Same users as casaos. Hashes are copied from casaos' passwd at cutover into
      # root-only files on the box (never into this repo). No ACLs there, so readwrite #.
      services.mosquitto = {
        enable = true;
        persistence = true;
        listeners = [
          {
            port = 1883;
            users = lib.genAttrs [ "zigbee2mqtt" "homeassistant" "dgmneto" ] (user: {
              hashedPasswordFile = "/etc/mosquitto-secrets/${user}.hash";
              acl = [ "readwrite #" ];
            });
          }
        ];
      };
      networking.firewall.allowedTCPPorts = [ 1883 ];
    })

    (lib.mkIf cfg.zigbee2mqtt.enable {
      # The module overwrites configuration.yaml from these settings on every start,
      # so anything z2m mutates (devices, groups) and every secret lives in separate
      # files in /var/lib/zigbee2mqtt, split out of the casaos config at cutover.
      services.zigbee2mqtt = {
        enable = true;
        settings = {
          version = 5;
          mqtt = {
            base_topic = "zigbee2mqtt";
            server = "mqtt://mosquitto:1883";
            user = "zigbee2mqtt";
            password = "!secret.yaml mqtt_password";
            retain = true;
          };
          # Network-attached SLZB-06M coordinator. Only ONE z2m may connect to it:
          # casaos' container must be `down` before this starts.
          serial = {
            port = "tcp://192.168.11.228:6638";
            adapter = "ember";
            baudrate = 115200;
            rtscts = false;
          };
          advanced = {
            log_level = "info";
            channel = 25;
            network_key = "!secret.yaml network_key";
            pan_id = "!secret.yaml pan_id";
            ext_pan_id = "!secret.yaml ext_pan_id";
            timestamp_format = "YYYY-MM-DD HH:mm:ss.SSS";
            log_console_json = true;
            log_debug_to_mqtt_frontend = false;
            log_directories_to_keep = 10;
          };
          frontend = {
            enabled = true;
            port = 8080;
          };
          homeassistant.enabled = true;
          devices = "devices.yaml";
          groups = "groups.yaml";
        };
      };
      networking.firewall.allowedTCPPorts = [ 8080 ];
    })

    (lib.mkIf cfg.matter.enable {
      # Fabric state goes in /var/lib/private/matter-server (DynamicUser). Pin the
      # interface so it never advertises on tailscale0.
      services.matter-server = {
        enable = true;
        openFirewall = true;
        extraArgs.primary-interface = "enp2s0";
      };
    })

    (lib.mkIf cfg.homeAssistant.enable {
      services.home-assistant = {
        enable = true;
        # nixos-26.05 ships 2026.5.x; casaos' config is from 2026.10.4 and HA can't
        # load a config from a newer version. Take HA from unstable until stable catches up.
        package = pkgsUnstable.home-assistant;
        # Keep the UI-managed configuration.yaml copied from casaos (trusted_proxies
        # must list the proxies' LAN IPs: nginxProd 192.168.14.33, nginxIntern .34).
        config = null;
        extraComponents = [
          "default_config"
          "analytics"
          "apple_tv"
          "backup"
          "cast"
          "co2signal"
          "go2rtc"
          "google_translate"
          "homekit"
          "matter"
          "met"
          "mobile_app"
          "mqtt"
          "radio_browser"
          "shopping_list"
          "smlight"
          "sonos"
          "thread"
          "unifiprotect"
          "webostv"
          "zha"
        ];
        customComponents = with pkgsUnstable.home-assistant-custom-components; [
          # Config entry exists on casaos but its code folder went missing; this restores it.
          octopus_energy
        ];
        # hacs, espsomfy_rts and zoned_heating stay as plain dirs in
        # /var/lib/hass/custom_components (copied from casaos; the module only prunes
        # symlinks). Nix HA can't pip-install, so provide their requirements here.
        extraPackages = ps: with ps; [
          aiogithubapi
          aiofiles
          websocket-client
        ];
      };
      # 8123 UI, 21064 HomeKit bridge ("HASS Bridge"), 5353 mDNS for discovery.
      networking.firewall.allowedTCPPorts = [ 8123 21064 ];
      networking.firewall.allowedUDPPorts = [ 5353 ];
    })
  ];
}
