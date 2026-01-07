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
        python = pkgs.python3;
        bibchecker = python.pkgs.buildPythonApplication {
          pname = "bibchecker";
          version = "0.1.0";
          src = ./.;
          pyproject = true;
          build-system = with python.pkgs; [ setuptools ];
          propagatedBuildInputs = with python.pkgs; [
            beautifulsoup4
            requests
            docopt
          ];
          nativeBuildInputs = with python.pkgs; [
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
          buildInputs = with python.pkgs; [
            python
            beautifulsoup4
            requests
            docopt
            mypy
          ];
        };
      }
    );
}
