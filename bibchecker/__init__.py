#!/usr/bin/env python3
""" usage: bibchecker [options] [IDS...]

options:
    --all               show all libraries even when media which cannot be borrowed (default is to only show libraries which have book available)
    --only-available    show books only if they are actually available (default is to print all books)
    --bib=BIB1,BIB2...  filter for specific libraries, skip the rest
    --sort-by=THING     sort by: item, bib [Default: item]
    --format=FORMAT     print format plain,html [Default: plain]
    -f=FILE             input file with all the IDs to supervise.
                        format will ignore all lines starting with hash-sign
                        input file will ignore all IDs given via cli
    --save-db=FILE      save parsed data as JSON to database file
    --load-db=FILE      load data from JSON database instead of fetching

input file format example:

    # super cool books
    AK00119197

    # super cool games
    SAK02110593 space escape
    SAK02174818 zeitstrudel
    # ende

"""
import json
from bs4 import BeautifulSoup
from pprint import pprint
import requests  # type: ignore[import-untyped]
from docopt import docopt
from typing import Iterable, Dict, Any, Optional, Generator, List
from collections import defaultdict

#url="https://opac.sbs.stuttgart.de/aDISWeb/app?service=direct/0/Home/$DirectLink&sp=SOPAC&sp={id}"
url="https://stadtbibliothek-stuttgart.de/aDISWeb/app?service=direct%2F0%2FHome%2F%24DirectLink&sp=SOPAC&sp={id}"

def parse_all_ids(ids:Iterable[str] ) -> Iterable[Dict[str,Any]]:
    for id in ids:
        yield parseid(id)

def parseid(ident: str) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"id": ident}
    #print(url.format(id=ident))
    ret = requests.get(url.format(id=ident))
    data = BeautifulSoup(ret.text, features="html.parser")
    tab = data.find("table", {"class": "gi"})
    if tab is not None:
        for row in tab.find_all('tr'):
            try:
                right_elem = row.find("td", {"class": "spalterechts"})
                left_elem = row.find("th")
                if right_elem is None or left_elem is None:
                    continue
                right = right_elem.get_text().strip()
                left = left_elem.get_text().strip()
                if left.startswith("Titel"):  # cleanup for broken html
                    left = "Titel"
                    try:
                        entry["Titel"], entry["TitelExtra"] = right.replace("Titel ", "").split(" / ")
                    except:
                        entry["Titel"] = right
                elif left:
                    entry[left] = right
            except:
                pass
            #print(row)
    tab = data.find("table", {"class": "rTable_table"})
    av: List[Dict[str, Any]] = []
    row_mapping = {
            "Bibliothek": "bib",
            "Standort": "standort",
            "Signatur": "sig",
            "Bestellmöglichkeit": "method",
            "Verfügbarkeit": "available",
            "Reservierung": "reservation",
            }
    available_rows: List[str] = []
    if tab is not None:
        thead = tab.find('thead')
        tbody = tab.find('tbody')
        if thead is not None:
            for row in thead.find_all('th'):
                row_text = row.get_text().strip()
                available_rows.append(row_mapping[row_text])

        if tbody is not None:
            for row in tbody.find_all('tr'):
                item: Dict[str, Any] = {}
                for idx, col in enumerate(row.find_all('td')):
                    item[available_rows[idx]] = col.get_text().strip()
                available = item.get('available', '')

                # available.startswith("Heute zurückgebucht")
                if available.startswith("Ausgeliehen") or \
                   available.startswith("Ist nur vor Ort nutzbar") or \
                   available.startswith("Nicht im Regal") or \
                   available.startswith("noch nicht im Haus") or \
                   available.startswith("Reserviert") or \
                   available.startswith("zur Zeit vermisst"):
                    item['can_be_borrowed'] = False
                else:
                    item['can_be_borrowed'] = True

                av.append(item)

    entry['status'] = av

    return entry

def load_ids(f: str) -> Generator[str, None, None]:
    with open(f) as fd:
        for line in fd.readlines():
            line = line.split(" ")[0].upper().strip()
            if line.startswith("#"):
                continue
            elif not line:
                continue
            elif line.startswith("AK"):
                line = f"S{line}"
                yield line
            elif line.startswith('javascript:htmlOnLink'):
                line = line.split("'")[1]
                yield line
            elif not line.startswith("SAK"):
                print("cannot parse line '{line}' - not starting with SAK or AK")
            else:
                yield line
def filter_ids(iddata: Iterable[Dict[str, Any]], all_data: bool = False, only_available: bool = False, bibfilter: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
    if not bibfilter:
        bibfilter = []
    for entry in iddata:

        # filter out entries from status if unwanted
        entry['status'] = [av for av in entry['status'] if (av.get('can_be_borrowed') or all_data) and ((av.get('bib') in bibfilter) or (not bibfilter))]
        # skip entries with no libraries where the book can be borrowed or only_available is unset
        if not only_available or entry['status']:
            yield entry


def update_input_file(filename: str, entries: List[Dict[str, Any]]) -> None:
    """Update the input file with titles from parsed entries."""
    # Build a mapping from ID to title
    id_to_title: Dict[str, str] = {}
    for entry in entries:
        eid = entry.get('id', '')
        title = entry.get('Titel', '')
        if eid and title:
            id_to_title[eid] = title
            # Also map without 'S' prefix for AK entries
            if eid.startswith('SAK'):
                id_to_title[eid[1:]] = title  # AK version

    # Read original file and update lines
    with open(filename, 'r') as fd:
        lines = fd.readlines()

    updated_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            updated_lines.append(line)
            continue

        # Extract the ID (first word)
        parts = stripped.split(' ', 1)
        raw_id = parts[0].upper()

        # Normalize ID
        if raw_id.startswith('AK'):
            lookup_id = f'S{raw_id}'
        elif raw_id.startswith('javascript:htmlOnLink'):
            lookup_id = raw_id.split("'")[1]
        else:
            lookup_id = raw_id

        # Update with title if found
        if lookup_id in id_to_title:
            updated_lines.append(f'{parts[0]} {id_to_title[lookup_id]}\n')
        else:
            updated_lines.append(line)

    # Write back
    with open(filename, 'w') as fd:
        fd.writelines(updated_lines)


def plain_print(iddata: Iterable[Dict[str, Any]], all_ids: List[str], sort_by: str = "item") -> None:
    if sort_by == "item":
        for entry in iddata:
            try:
                print()
                print(f"{entry['Titel']}")
            except Exception as e:
                print(f"!! problem with {entry}")
                continue

            for av in entry['status']:
                print(f"  {av.get('bib')} ({av.get('standort') or 'No Data'}) - {av.get('available')}")
    elif sort_by == "bib":
        print(f"Gathering {len(all_ids)} entries first ... please wait")
        bib_entries: Dict[str, List[Dict[str, Any]]] = {}
        for ident, entry in enumerate(iddata):
            print(ident, end=" ", flush=True)
            for status in entry['status']:
                status['entry'] = entry
                bib = status.get('bib', 'Unknown')
                if bib not in bib_entries:
                    bib_entries[bib] = []
                bib_entries[bib].append(status)

        print("done")
        for k, vals in bib_entries.items():
            print()
            print(f"Library '{k}'")

            for v in vals:
                entry = v['entry']
                print(f"  {entry['Titel']} - {v.get('standort')} - {v.get('available')}")


def html_print(iddata: Iterable[Dict[str, Any]], all_ids: List[str], sort_by: str = "item") -> None:
    from datetime import datetime
    html_parts: List[str] = []
    
    # Compact HTML with minimal CSS
    html_parts.append("""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Bibliothek Status</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 15px; }
        table { border-collapse: collapse; width: 100%; background: white; }
        th { background: #eee; text-align: left; padding: 8px; border-bottom: 2px solid #999; }
        td { padding: 6px 8px; border-bottom: 1px solid #eee; vertical-align: top; }
        .title { font-weight: 600; background: #fafafa; border-top: 2px solid #666; }
        .first { border-top: 2px solid #666; }
        .ok { color: #228b22; font-weight: 600; }
        .no { color: #dc143c; }
        .loc { color: #888; font-size: 0.9em; }
        .ts { color: #999; font-size: 0.8em; margin-top: 20px; }
    </style>
</head>
<body>
<h1>📚 Stadtbibliothek Stuttgart</h1>
<table>
<tr><th>Titel</th><th>Bibliothek</th><th>Standort</th><th>Status</th></tr>
""")

    if sort_by == "item":
        for entry in iddata:
            title = entry.get('Titel', 'Unbekannt')
            statuses = entry.get('status', [])
            if statuses:
                for i, av in enumerate(statuses):
                    bib = av.get('bib', '?')
                    loc = av.get('standort') or '-'
                    avail = av.get('available', '?')
                    cls = 'ok' if av.get('can_be_borrowed') else 'no'
                    if i == 0:
                        html_parts.append(f'<tr><td class="title" rowspan="{len(statuses)}">{title}</td><td class="first">{bib}</td><td class="first loc">{loc}</td><td class="first {cls}">{avail}</td></tr>\n')
                    else:
                        html_parts.append(f'<tr><td>{bib}</td><td class="loc">{loc}</td><td class="{cls}">{avail}</td></tr>\n')
            else:
                html_parts.append(f'<tr><td class="title">{title}</td><td colspan="3" class="first no">Keine Daten</td></tr>\n')

    elif sort_by == "bib":
        bib_entries: Dict[str, List[Dict[str, Any]]] = {}
        for entry in iddata:
            for status in entry['status']:
                status['entry'] = entry
                bib = status.get('bib', 'Unbekannt')
                if bib not in bib_entries:
                    bib_entries[bib] = []
                bib_entries[bib].append(status)

        for library, items in sorted(bib_entries.items()):
            html_parts.append(f'<tr><td colspan="4" style="background:#ddd;font-weight:600;padding:10px;">🏛️ {library}</td></tr>\n')
            for item in items:
                entry = item.get('entry', {})
                title = entry.get('Titel', 'Unbekannt')
                loc = item.get('standort') or '-'
                avail = item.get('available', '?')
                cls = 'ok' if item.get('can_be_borrowed') else 'no'
                html_parts.append(f'<tr><td class="title">{title}</td><td>-</td><td class="loc">{loc}</td><td class="{cls}">{avail}</td></tr>\n')

    html_parts.append('</table>\n')
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    html_parts.append(f'<div class="ts">Stand: {timestamp}</div>\n</body></html>')
    
    print("".join(html_parts))
            



def save_database(filename: str, entries: List[Dict[str, Any]]) -> None:
    """Save entries to JSON database file."""
    with open(filename, 'w', encoding='utf-8') as fd:
        json.dump(entries, fd, ensure_ascii=False, indent=2)


def load_database(filename: str) -> List[Dict[str, Any]]:
    """Load entries from JSON database file."""
    with open(filename, 'r', encoding='utf-8') as fd:
        data: List[Dict[str, Any]] = json.load(fd)
    return data


def main() -> None:
    args = docopt(__doc__)
    bibfilter = args['--bib'].split(',') if args['--bib'] else []

    input_file = args['-f']
    load_db = args['--load-db']
    save_db = args['--save-db']

    # Load data either from database or by fetching
    if load_db:
        all_entries = load_database(load_db)
        ids = [e.get('id', '') for e in all_entries]
    else:
        if input_file:
            ids = list(load_ids(input_file))
        else:
            ids = args['IDS']
        # Collect all entries first so we can both output and update the file
        all_entries = list(parse_all_ids(ids))

    # Save to database if requested
    if save_db:
        save_database(save_db, all_entries)

    filtered_data = list(filter_ids(iter(all_entries), args['--all'], args['--only-available'], bibfilter))
    # print(args)
    if args['--format'] == "plain":
        plain_print(iter(filtered_data), ids, args["--sort-by"])
    elif args['--format'] == "html":
        html_print(iter(filtered_data), ids, args["--sort-by"])

    # Update input file with titles (only if we fetched new data)
    if input_file and not load_db:
        update_input_file(input_file, all_entries)



if __name__ == "__main__":
    main()
