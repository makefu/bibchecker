"""Library parser modules."""
from typing import Dict, Any, List, Type

from bibchecker.base import LibraryParser
from bibchecker.parsers.stuttgart import StuttgartParser
from bibchecker.parsers.remseck import RemseckParser

# Registry of all available parsers
PARSERS: List[Type[LibraryParser]] = [
    StuttgartParser,
    RemseckParser,
]


def get_parser_for_id(ident: str) -> Type[LibraryParser]:
    """Find the appropriate parser for the given ID."""
    for parser in PARSERS:
        if parser.matches(ident):
            return parser
    raise ValueError(f"No parser found for ID: {ident}")


def parse_id(ident: str) -> Dict[str, Any]:
    """Parse an ID using the appropriate library parser."""
    parser = get_parser_for_id(ident)
    return parser.parse(ident)


def normalize_id(raw_id: str) -> str:
    """Normalize a raw ID using the appropriate parser."""
    for parser in PARSERS:
        if parser.matches(raw_id) or parser.matches(raw_id.upper()):
            return parser.normalize_id(raw_id)
    return raw_id
