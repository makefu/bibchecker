{ pkgs ? import <nixpkgs> {}}:

pkgs.mkShell {
  nativeBuildInputs = with pkgs.python38.pkgs;[ beautifulsoup4 requests docopt  ];
}
