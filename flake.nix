{
  description = "Checks Stuttgart stadtbibliothek";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        bibchecker = pkgs.python3Packages.buildPythonApplication {
          pname = "bibchecker";
          version = "0.1.0";
          src = ./.;
          propagatedBuildInputs = with pkgs.python3Packages; [
            beautifulsoup4
            requests
            docopt
          ];
          nativeBuildInputs = with pkgs.python3Packages; [
            mypy
          ];
          checkPhase = ''
            mypy bibchecker
          '';
        };
      in
      {
        packages.default = bibchecker;
        packages.bibchecker = bibchecker;

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs.python3Packages; [
            python3
            beautifulsoup4
            requests
            docopt
            mypy
          ];
        };
      }
    );
}
