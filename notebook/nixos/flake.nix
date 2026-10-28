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
  };

  outputs = { nixpkgs, hermes-agent, ... }: {
    nixosConfigurations.homelab-notebook = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        hermes-agent.nixosModules.default
        ./hardware-configuration.nix
        ./configuration.nix
        ./hermes.nix
      ];
    };
  };
}
