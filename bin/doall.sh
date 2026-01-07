#!/bin/sh
set -euf
mybibs="Bad Cannstatt,Feuerbach,Freiberg,Neugereut,Ost,Stadtbibliothek am Mailänder Platz,Zuffenhausen"
infile=${1:-STUFF}
outdir=${2:-out}
cachefile=$outdir/cache.json

mkdir -p "$outdir"
trap 'rm -f "$cachefile"' INT TERM EXIT


echo "Creating cachefile at $cachefile"
bibchecker -f "$infile"  --all --save-db "$cachefile" >/dev/null

# Generate per-library HTML files
jq -r '.[] | .status[] | .bib' "$cachefile" | sort | uniq | while read bib;do
    echo "$bib"
    bibchecker --format html --load-db "$cachefile" --bib="$bib" --only-available > "$outdir/${bib}.html"
done

bibchecker --format html --load-db "$cachefile" --bib="$mybibs" --sort-by=bib --only-available > "$outdir/mybibs.html"
bibchecker --format html --load-db "$cachefile" --all > "$outdir/all_items.html"
bibchecker --format html --load-db "$cachefile" --sort-by=bib --all > "$outdir/all_bib.html"

# Generate index.html
timestamp=$(date "+%d.%m.%Y %H:%M")
cat > "$outdir/index.html" << 'HEADER'
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Bibliothek Status - Übersicht</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 15px; }
        h2 { color: #444; margin: 20px 0 8px 0; padding-bottom: 4px; border-bottom: 1px solid #ddd; }
        table { border-collapse: collapse; width: 100%; background: white; }
        th { background: #eee; text-align: left; padding: 8px; border-bottom: 2px solid #999; }
        td { padding: 6px 8px; border-bottom: 1px solid #eee; }
        a { color: #2266cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .special { font-weight: 600; background: #fafafa; border-top: 2px solid #666; }
        .ts { color: #999; font-size: 0.8em; margin-top: 20px; }
    </style>
</head>
<body>
<h1>📚 Stadtbibliothek Stuttgart - Übersicht</h1>

<h2>Zusammenfassungen</h2>
<table>
<tr><th>Datei</th><th>Beschreibung</th></tr>
<tr class="special"><td><a href="mybibs.html">mybibs.html</a></td><td>Meine Bibliotheken (nur verfügbar)</td></tr>
<tr><td><a href="all_items.html">all_items.html</a></td><td>Alle Medien nach Titel</td></tr>
<tr><td><a href="all_bib.html">all_bib.html</a></td><td>Alle Medien nach Bibliothek</td></tr>
</table>

<h2>Nach Bibliothek</h2>
<table>
<tr><th>Bibliothek</th></tr>
HEADER

# Add library links
jq -r '.[] | .status[] | .bib' "$cachefile" | sort | uniq | while read bib;do
    echo "<tr><td><a href=\"${bib}.html\">$bib</a></td></tr>" >> "$outdir/index.html"
done

cat >> "$outdir/index.html" << FOOTER
</table>
<div class="ts">Stand: $timestamp</div>
</body>
</html>
FOOTER

echo "Generated index.html in $outdir"
