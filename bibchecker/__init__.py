#!/usr/bin/env python3
""" usage: bibchecker [options] [IDS...]

options:
    --all               show all availabilities, not only media which can be borrowed
    --only-available    only show available books
    --bib=BIB1,BIB2...  filter for specific libraries, skip the rest
    -f=FILE             input file with all the IDs to supervise.
                        format will ignore all lines starting with hash-sign
                        input file will ignore all IDs given via cli

input file format example:

# super cool books
AK00119197

# super cool games
SAK02110593 space escape
SAK02174818 zeitstrudel
# ende

"""
from bs4 import BeautifulSoup
from pprint import pprint
import requests
from docopt import docopt
from typing import Iterable,Dict,Any
from collections import defaultdict

#url="https://opac.sbs.stuttgart.de/aDISWeb/app?service=direct/0/Home/$DirectLink&sp=SOPAC&sp={id}"
url="https://stadtbibliothek-stuttgart.de/aDISWeb/app?service=direct%2F0%2FHome%2F%24DirectLink&sp=SOPAC&sp={id}"

def parse_all_ids(ids:Iterable[str] ) -> Iterable[Dict[str,Any]]:
    for id in ids:
        yield parseid(id)

def parseid(ident:str ) -> Dict[Any,Any]:
    entry:Dict[str,Any] = {"id":ident}
    #print(url.format(id=ident))
    ret = requests.get(url.format(id=ident))
    data = BeautifulSoup(ret.text,features="html.parser")
    tab = data.find("table",{"class":"gi"})
    for row in tab.find_all('tr'):
        try:
            right =row.find("td",{"class":"spalterechts"}).get_text().strip()
            left = row.find("th").get_text().strip()
            if left.startswith("Titel"): # cleanup for broken html
                left = "Titel"
                entry["Titel"],entry["TitelExtra"] = right.strip("Titel ").split(" / ")
            elif left:
                entry[left] = right
        except:
            pass
        #print(row)
    tab = data.find("table",{"class":"rTable_table"})
    av = []
    row_mapping = {
            "Bibliothek":"bib",
            "Standort":"standort",
            "Signatur":"sig",
            "Bestellmöglichkeit":"method",
            "Verfügbarkeit": "available",
            "Reservierung": "reservation",
            }
    available_rows = []
    for row in tab.find('thead').find_all('th'):
        row = row.get_text().strip()
        # print(row)
        available_rows.append(row_mapping[row])
    for row in tab.find('tbody').find_all('tr'):
        item = defaultdict(lambda: None) 
        for idx,col in enumerate(row.find_all('td')):
            item[available_rows[idx]] = col.get_text().strip()
        #pprint(item)
        available =  item['available']


        if available.startswith("Ausgeliehen") or \
           available.startswith("Ist nur vor Ort nutzbar") or \
           available.startswith("Nicht im Regal") or \
           available.startswith("zur Zeit vermisst"):
            item['can_be_borrowed'] = False
        else:
            item['can_be_borrowed'] = True

        av.append(item)

    entry['status'] = av
    #from pprint import pprint
    #pprint(entry)

    return entry

def load_ids(f:str):
    with open(f) as fd:
        for line in fd.readlines():
            line = line.split(" ")[0].upper().strip()
            if line.startswith("#"):
                continue
            if not line:
                continue
            if line.startswith("AK"):
                line = f"S{line}"
            if not line.startswith("SAK"):
                print("cannot parse line '{line}' - not starting with SAK or AK")
            else:
                yield line

def main() -> None:
    args = docopt(__doc__)
    bibfilter = args['--bib'].split(',') if args['--bib'] else []

    if  args['-f']:
        ids = list(load_ids(args['-f']))
    else:
        ids = args['IDS']
    print(ids)

    for entry in parse_all_ids(ids):
        status = [ av for av in entry['status'] if (av['can_be_borrowed'] or args['--all']) and ((av['bib'] in bibfilter) or (not bibfilter)) ]
        if not args['--only-available'] or status:
            print(f"{entry['id']}: {entry['Titel']}")

        for av in status:
            print(f"  {av['bib']} ({av['standort'] or 'No Data'}) - {av['available']}")

if __name__ == "__main__":
    main()
