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
        doallScript = ./bin/doall.sh;
        bibchecker-python = python.pkgs.buildPythonApplication {
          pname = "bibchecker";
          version = "0.1.0";
          src = ./.;
          pyproject = true;
          build-system = with python.pkgs; [ setuptools ];
          propagatedBuildInputs = with python.pkgs; [
            beautifulsoup4
            requests
            docopt
            flask
            apscheduler
          ];
          nativeBuildInputs = with python.pkgs; [
            mypy
          ];
          checkPhase = ''
            mypy bibchecker
          '';
        };
        bibchecker = pkgs.symlinkJoin {
          name = "bibchecker-with-scripts";
          paths = [ bibchecker-python ];
          buildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            mkdir -p $out/bin
            cp ${doallScript} $out/bin/doall.sh
            chmod +x $out/bin/doall.sh
            wrapProgram $out/bin/doall.sh \
              --prefix PATH : ${pkgs.lib.makeBinPath [ bibchecker-python pkgs.jq ]}

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
            flask
            apscheduler
            docopt
            mypy
          ];
        };
      }
    );
}
