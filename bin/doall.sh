#!/bin/sh
set -euf
mybibs="Bad Cannstatt,Feuerbach,Freiberg,Neugereut,Ost,Stadtbibliothek am Mailänder Platz,Zuffenhausen"
cachefile=$(mktemp)

trap 'rm -f "$cachefile"' INT TERM EXIT

bibchecker -f STUFF  --all --save-db "$cachefile"

for bib in $(jq -r '.[] | .status[] | .bib' "$cachefile" | sort | uniq);do
    echo "$bib"
    bibchecker --format html --load-db "$cachefile" --bib="$bib" --only-available > "${bib}.html"
done

bibchecker --format html --load-db "$cachefile" --bib="$mybibs" --sort-by=bib --only-available > mybibs.html
bibchecker --format html --load-db "$cachefile" --all > all_items.html
bibchecker --format html --load-db "$cachefile" --sort-by=bib --all > all_bib.html
