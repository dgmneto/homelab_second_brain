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
  # The module sets HERMES_MANAGED, which makes Hermes refuse every config
  # write (config set/edit, .env, plugin settings), not just the keys pinned
  # in `settings`. Opt out so the agent can update its own config.yaml.
  # The .managed marker still applies to interactive shells (admin CLI).
  hermesUnmanaged = { HERMES_MANAGED = lib.mkForce "false"; };
in
{
  services.hermes-agent = {
    enable = true;
    # stateDir = /var/lib/hermes; HERMES_HOME = /var/lib/hermes/.hermes
    addToSystemPackages = true;

    # Secrets (OPENROUTER_API_KEY, TELEGRAM_*, HERMES_DASHBOARD_BASIC_AUTH_*,
    # API_SERVER_KEY). Plain 0600 file, not in git. TODO: move to sops-nix.
    environmentFiles = [ "/var/lib/hermes/env" ];

    # Only the keys we want pinned (re-applied on every rebuild); everything
    # else in config.yaml is agent-managed on disk. The model is deliberately
    # unpinned so Hermes can switch it; the last pinned value (openrouter,
    # qwen/qwen3.8-max) stays in config.yaml.
    settings = {
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
      openssh # ssh casaos (see "casaos access" below)
      git # second brain clone at /var/lib/hermes/home/homelab
      # coding
      gh # needs GH_TOKEN in env file for API work; git itself uses SSH
      ripgrep
      fd
      gnumake
      gcc
      nodejs
    ];
  };

  # --- casaos access + second brain -------------------------------------
  # Hermes SSHes to casaos as user `hermes` (docker group, rwX ACL on
  # /home/dgmneto/homelab, no sudo) and pushes the second-brain repo
  # (github dgmneto/homelab_second_brain) with a repo-scoped deploy key.
  # Keys are generated on the box and never leave it; casaos side is set up
  # by hand (see homelab_second_brain services/hermes/README.md).
  # id_github is for coding: added to dgmneto's own GitHub account, so it can
  # push to every repo dgmneto can. Revoke at github.com/settings/keys.
  systemd.services.hermes-ssh-keys = {
    description = "Generate Hermes SSH keys if missing";
    wantedBy = [ "hermes-agent.service" ];
    before = [ "hermes-agent.service" ];
    path = [ pkgs.openssh ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      User = "hermes";
    };
    script = ''
      install -d -m 700 /var/lib/hermes/.ssh
      for k in casaos github_brain github; do
        f=/var/lib/hermes/.ssh/id_$k
        [ -e "$f" ] || ssh-keygen -q -t ed25519 -N "" -C "hermes@homelab-notebook ($k)" -f "$f"
      done
    '';
  };

  # ssh reads ~/.ssh from the passwd home (/var/lib/hermes), not $HOME, so
  # pin everything here instead.
  programs.ssh.extraConfig = ''
    Match localuser hermes host casaos,homelab,192.168.11.13
      HostName 192.168.11.13
      User hermes
      IdentityFile /var/lib/hermes/.ssh/id_casaos
      IdentitiesOnly yes
    # GitHub takes the first registered key offered, so the account key wins
    # once added; the brain deploy key stays as fallback until it is.
    Match localuser hermes host github.com
      IdentityFile /var/lib/hermes/.ssh/id_github
      IdentityFile /var/lib/hermes/.ssh/id_github_brain
      IdentitiesOnly yes
  '';
  programs.ssh.knownHosts = {
    casaos = {
      hostNames = [ "casaos" "homelab" "192.168.11.13" ];
      publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBxYWEfoHxVn+vZRSFCbn14/EbX31lhVh6obxpumvldr";
    };
    github = {
      hostNames = [ "github.com" ];
      publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl";
    };
  };

  # Same limits the container had.
  systemd.services.hermes-agent.serviceConfig = {
    MemoryMax = "2G";
    CPUQuota = "100%";
    TasksMax = 256;
    # Gateway drains for up to restart_drain_timeout (180s) + cron (30s).
    TimeoutStopSec = 240;
  };
  systemd.services.hermes-agent.environment = hermesEnv // hermesUnmanaged // {
    GIT_AUTHOR_NAME = "Hermes";
    GIT_AUTHOR_EMAIL = "hermes@homelab-notebook";
    GIT_COMMITTER_NAME = "Hermes";
    GIT_COMMITTER_EMAIL = "hermes@homelab-notebook";
    # Rewrite https GitHub URLs to SSH so cloned repos can be pushed.
    GIT_CONFIG_COUNT = "1";
    GIT_CONFIG_KEY_0 = "url.git@github.com:.insteadOf";
    GIT_CONFIG_VALUE_0 = "https://github.com/";
  };
  systemd.services.hermes-backend.environment = hermesEnv // hermesUnmanaged;

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
