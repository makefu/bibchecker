"""Filtering utilities for bibchecker."""
from typing import Dict, Any, List, Optional, Iterable, Generator


def filter_ids(
    iddata: Iterable[Dict[str, Any]],
    all_data: bool = False,
    only_available: bool = False,
    bibfilter: Optional[List[str]] = None,
) -> Generator[Dict[str, Any], None, None]:
    """Filter entries based on availability and library criteria."""
    if not bibfilter:
        bibfilter = []

    for entry in iddata:
        # Filter out entries from status if unwanted
        entry["status"] = [
            av
            for av in entry["status"]
            if (av.get("can_be_borrowed") or all_data)
            and ((av.get("bib") in bibfilter) or (not bibfilter))
        ]
        # Skip entries with no libraries where the book can be borrowed or only_available is unset
        if not only_available or entry["status"]:
            yield entry
