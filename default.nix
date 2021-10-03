
{ pkgs ? import <nixpkgs> {}}:

pkgs.python3Packages.buildPythonApplication {
  pname = "bibchecker";
  version = "0.1.0";
  src = ./.;
  propagatedBuildInputs = with pkgs.python3Packages; [
    beautifulsoup4 requests docopt
  ];
  nativeBuildInputs = with pkgs.python3Packages; [
    mypy
  ];
  checkPhase = ''
    mypy bibchecker
  '';
}
