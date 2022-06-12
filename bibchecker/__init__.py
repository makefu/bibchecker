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
    for row in tab.find('tbody').find_all('tr'):
        try:
            bib,standort,sig,available,reservation = [ a.get_text().strip() for a in row.find_all('td') ]
        except:
            bib,standort,available,reservation = [ a.get_text().strip() for a in row.find_all('td') ]
            sig = None
        if available.startswith("Ausgeliehen") or available.startswith("Ist nur vor Ort nutzbar") or available.startswith("Nicht im Regal"):
            can_be_borrowed = False
        else:
            can_be_borrowed = True
        av.append({
                "bib": bib,
                "standort": standort,
                "sig":sig,
                "available":available,
                "can_be_borrowed": can_be_borrowed,
                "reservation":reservation
                })

    entry['status'] = av

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
            print(f"  {av['bib']} - {av['available']}")

if __name__ == "__main__":
    main()
