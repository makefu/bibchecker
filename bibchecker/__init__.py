"""
bibchecker - Check library availability for items.

Supports:
  - Stuttgart (Stadtbibliothek Stuttgart): IDs starting with SAK or AK
  - Remseck (Mediathek Remseck): Numeric IDs
"""
from bibchecker.cli import main, parse_all_ids
from bibchecker.parsers import parse_id, PARSERS
from bibchecker.output import plain_print, html_print
from bibchecker.database import save_database, load_database
from bibchecker.filters import filter_ids
from bibchecker.input import load_ids, update_input_file


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
