# Bibchecker
 Simple script which checks the Stadtbibliothek Stuttgart Website if Media can be borrowed

# Usage
## NixOS
 ```
$ nix-shell --run 'python ./bibchecker.py SAK02068634'
SAK02068634: Hello World : Was Algorithmen können und wie sie unser Leben verändern
  Stadtbibliothek am Mailänder Platz - Ausleihbar
  Vaihingen - Ausleihbar
  Weilimdorf - Ausleihbar
```
## Other OS
install the python libraries `beautifulsoup4` `requests` `docopt` for
python38, run `python bibchecker.py SAK02068634`
