#!/usr/bin/env python3
"""
bibchecker - Check library availability for items.

Usage:
  bibchecker [options] [IDS...]

Options:
  -f=FILE              Input file with IDs to check
  --all                Display non-borrowable items as well
  --only-available     Only show items that are available in at least one location
  -h --help            Show this help
  --bib=BIB            Filter for a list of libraries (comma-separated)
  --format=FORMAT      Output format: plain, html [default: plain]
  --sort-by=SORT       Sort by item or bib [default: item]
  --update             Update input file with fetched titles
  --save-db=FILE       Save fetched data to JSON file
  --load-db=FILE       Load data from JSON file instead of fetching

Examples:
  bibchecker -f mybooks.txt
  bibchecker --format html -f mybooks.txt > report.html
  bibchecker -f mybooks.txt --save-db=cache.json
  bibchecker --load-db=cache.json --format html

Supported libraries:
  - Stuttgart (Stadtbibliothek Stuttgart): IDs starting with SAK or AK
  - Remseck (Mediathek Remseck): Numeric IDs
"""
from docopt import docopt  # type: ignore[import-untyped]
from typing import Dict, Any, List, Generator

# Import from modules
from bibchecker.parsers import parse_id, PARSERS
from bibchecker.output import plain_print, html_print
from bibchecker.database import save_database, load_database
from bibchecker.filters import filter_ids
from bibchecker.input import load_ids, update_input_file


def parse_all_ids(ids: List[str]) -> Generator[Dict[str, Any], None, None]:
    """Parse all IDs and yield entry dicts."""
    for ident in ids:
        try:
            yield parse_id(ident)
        except ValueError as e:
            print(f"Error: {e}")
            continue


def main() -> None:
    """Main entry point."""
    args = docopt(__doc__)

    # Load entries from database or fetch from web
    if args["--load-db"]:
        entries = load_database(args["--load-db"])
        all_ids: List[str] = [e["id"] for e in entries]
    else:
        input_file = args["-f"]
        if input_file:
            all_ids = list(load_ids(input_file))
        else:
            all_ids = args["IDS"]
        entries = list(parse_all_ids(all_ids))

    # Save to database if requested
    if args["--save-db"]:
        save_database(args["--save-db"], entries)

    # Update input file if requested
    if args["--update"] and args["-f"]:
        update_input_file(args["-f"], entries)

    # Parse filter options
    bibfilter: List[str] = []
    if args["--bib"]:
        bibfilter = [b.strip() for b in args["--bib"].split(",")]

    # Apply filters
    filtered_entries = filter_ids(
        entries,
        all_data=args["--all"],
        only_available=args["--only-available"],
        bibfilter=bibfilter,
    )

    # Output
    if args["--format"] == "html":
        html_print(filtered_entries, all_ids, args["--sort-by"])
    else:
        plain_print(filtered_entries, all_ids, args["--sort-by"])


# Export public API
__all__ = [
    "main",
    "parse_all_ids",
    "parse_id",
    "load_ids",
    "filter_ids",
    "plain_print",
    "html_print",
    "save_database",
    "load_database",
    "update_input_file",
    "PARSERS",
]


if __name__ == "__main__":
    main()
