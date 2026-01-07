"""Database operations for bibchecker."""
import json
from typing import Dict, Any, List


def save_database(filename: str, entries: List[Dict[str, Any]]) -> None:
    """Save entries to JSON database file."""
    with open(filename, "w", encoding="utf-8") as fd:
        json.dump(entries, fd, ensure_ascii=False, indent=2)


def load_database(filename: str) -> List[Dict[str, Any]]:
    """Load entries from JSON database file."""
    with open(filename, "r", encoding="utf-8") as fd:
        data: List[Dict[str, Any]] = json.load(fd)
    return data
