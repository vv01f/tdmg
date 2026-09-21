{
  description = "Musikalisches Gehörtraining";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      name = "tdmg";
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems =
        function:
        nixpkgs.lib.genAttrs systems (
          system:
          function {
            pkgs = import nixpkgs { inherit system; };
          }
        );
    in
    {
      packages = forAllSystems (
        { pkgs }:
        {
          default = pkgs.callPackage ./package.nix { };
        }
      );

      apps = forAllSystems (
        { pkgs }:
        {
          default = {
            type = "app";
            program = "${self.packages.${pkgs.system}.default}/bin/${name}";
          };
        }
      );

      devShells = forAllSystems (
        { pkgs }:
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              python3
              python3Packages.numpy
              python3Packages.sounddevice
              nixfmt
              ruff
              portaudio
              tk
            ];

            shellHook = ''
              echo "tdmg development shell"
              echo "  nix build"
              echo "  nix run"
              echo "  nix develop"
              echo "  nix fmt"
            '';
          };
        }
      );

      formatter = forAllSystems (
        { pkgs }:
        pkgs.writeShellApplication {
          name = "format";

          runtimeInputs = [
            pkgs.nixfmt
            pkgs.ruff
          ];

          text = ''
            set -euo pipefail

            nixfmt package.nix flake.nix

            ruff format .
          '';
        }
      );
    };
}
