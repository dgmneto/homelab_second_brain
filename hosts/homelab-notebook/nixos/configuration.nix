{ pkgs, ... }:

let
  # Private key lives only in 1Password ("homelab-notebook SSH").
  adminKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMFVgkdtR5UfrkplCtZVgwbCHl45R15EZLbmNjSfpemF";
in
{
  # Boot: systemd-boot on UEFI, keep last 10 generations for rollback.
  boot.loader.systemd-boot.enable = true;
  boot.loader.systemd-boot.configurationLimit = 10;
  boot.loader.efi.canTouchEfiVariables = true;

  # Network
  networking.hostName = "homelab-notebook";
  networking.networkmanager.enable = true;
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [ 22 ];
  };

  time.timeZone = "Europe/London";
  i18n.defaultLocale = "en_GB.UTF-8";
  console.keyMap = "us";

  # Admin user: SSH key only, no password.
  users.mutableUsers = false;
  users.users.dgmneto = {
    isNormalUser = true;
    extraGroups = [ "wheel" "networkmanager" ];
    openssh.authorizedKeys.keys = [ adminKey ];
  };
  # Agent account for Claude sessions: no password/keys, reached via Tailscale SSH
  # (tailnet policy: tag:claude -> tag:server as "claude"). Passwordless sudo via wheel.
  users.users.claude = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
  };
  security.sudo.wheelNeedsPassword = false;

  # Tailscale: tagged tag:server node with Tailscale SSH. Joined once by hand with a
  # one-off auth key (see services/tailscale/README.md); no subnet routes (casaos does that).
  services.tailscale = {
    enable = true;
    openFirewall = true;
    extraSetFlags = [ "--ssh" "--accept-dns=false" "--operator=dgmneto" ];
  };

  # SSH: keys only, no root.
  services.openssh = {
    enable = true;
    settings = {
      PasswordAuthentication = false;
      KbdInteractiveAuthentication = false;
      PermitRootLogin = "no";
    };
  };

  # Laptop as server: never sleep, ignore lid.
  services.logind.settings.Login = {
    HandleLidSwitch = "ignore";
    HandleLidSwitchExternalPower = "ignore";
    HandleLidSwitchDocked = "ignore";
  };
  systemd.sleep.settings.Sleep = {
    AllowSuspend = "no";
    AllowHibernation = "no";
    AllowHybridSleep = "no";
    AllowSuspendThenHibernate = "no";
  };

  hardware.enableRedistributableFirmware = true;

  # Nix: flakes, weekly cleanup, dedupe store.
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    auto-optimise-store = true;
    trusted-users = [ "dgmneto" ];
  };
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 30d";
  };

  environment.systemPackages = with pkgs; [ git vim htop ];

  system.stateVersion = "26.05";
}
