{
  description = "homelab-notebook NixOS configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    # Pinned to the version that ran in Docker on casaos (v0.21.5, 2026.9.24).
    # Upstream Nix support is best-effort; bump deliberately.
    hermes-agent.url = "github:NousResearch/hermes-agent/749220ef0007f8d87bd1531f1c24b0fe93816385";
    # Share system nixpkgs: the notebook (3.6 GB RAM) swaps to death evaluating
    # a second nixpkgs. Not the combination upstream tests; revisit with more RAM.
    hermes-agent.inputs.nixpkgs.follows = "nixpkgs";
    # Only for packages stable is too old for (home-assistant: casaos runs 2026.10.x).
    # Lazily evaluated, so it costs nothing until a module uses it. RAM is 11.7 GB now.
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { nixpkgs, nixpkgs-unstable, hermes-agent, ... }:
    let
      system = "x86_64-linux";
      mkHost = extraModules: nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs.pkgsUnstable = nixpkgs-unstable.legacyPackages.${system};
        modules = [
          hermes-agent.nixosModules.default
          ./hardware-configuration.nix
          ./configuration.nix
          ./hermes.nix
          ./pihole.nix
          ./home-automation.nix
        ] ++ extraModules;
      };
    in
    {
      # Migration progress: flip one service per phase (services/homeassistant/MIGRATION.md).
      nixosConfigurations.homelab-notebook = mkHost [
        { homelab.homeAutomation.mosquitto.enable = true; }
      ];
      # Build-only (never switch to it): the whole home-automation stack enabled, so
      # `nix build` pre-fetches/compiles it before each migration phase.
      nixosConfigurations.homelab-notebook-ha-preview = mkHost [
        {
          homelab.homeAutomation = {
            mosquitto.enable = true;
            zigbee2mqtt.enable = true;
            matter.enable = true;
            homeAssistant.enable = true;
          };
        }
      ];
    };
}
