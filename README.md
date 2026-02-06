# Bibchecker
 Simple script which checks the Stadtbibliothek Stuttgart Website if Media can be borrowed

# Usage
` bibchecker.py --help`

## NixOS
 ```
$ nix-build && result/bin/bibchecker SAK02068634
SAK02068634: Hello World : Was Algorithmen können und wie sie unser Leben verändern
  Stadtbibliothek am Mailänder Platz - Ausleihbar
  Vaihingen - Ausleihbar
  Weilimdorf - Ausleihbar
```

## Other OS

Install `setuptools` python dependency.
To build and install run the command: `python setup.py develop`
For testing you can execute `bibchecker SAK02068634`.

# License
MIT ( see LICENSE)
