"""Input file handling for bibchecker."""
from typing import Dict, Any, List, Generator

from bibchecker.parsers import normalize_id


def load_ids(f: str) -> Generator[str, None, None]:
    """Load and normalize IDs from an input file."""
    with open(f) as fd:
        for line in fd.readlines():
            raw_line = line.split(" ")[0].strip()
            if not raw_line or raw_line.startswith("#"):
                continue

            # Try to normalize the ID
            normalized = normalize_id(raw_line)
            if normalized:
                yield normalized
            else:
                print(f"cannot parse line '{raw_line}' - unknown ID format")


def load_user_description(f: str) -> Generator[tuple[str, str], None, None]:
    """Load user description from an input file."""
    with open(f) as fd:
        for line in fd.readlines():
            raw_line = line.split(" ")[0].strip()
            if not raw_line or raw_line.startswith("#"):
                continue

            # Try to normalize the ID
            normalized = normalize_id(raw_line)
            if normalized:
                yield normalized, ' '.join(line.split()[1:]) if ' ' in line else None
            else:
                print(f"cannot parse line '{raw_line}' - unknown ID format")


def update_input_file(filename: str, entries: List[Dict[str, Any]]) -> None:
    """Update the input file with titles from parsed entries."""
    # Build a mapping from ID to title
    id_to_title: Dict[str, str] = {}
    for entry in entries:
        eid = entry.get("id", "")
        title = entry.get("Titel", "")
        if eid and title:
            id_to_title[eid] = title
            id_to_title[eid.lower()] = title
            id_to_title[eid.upper()] = title
            # Also map without 'S' prefix for AK entries
            if eid.upper().startswith("SAK"):
                id_to_title[eid[1:]] = title
                id_to_title[eid[1:].upper()] = title

    # Read original file and update lines
    with open(filename, "r") as fd:
        lines = fd.readlines()

    updated_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            updated_lines.append(line)
            continue

        # Extract the ID (first word)
        parts = stripped.split(" ", 1)
        raw_id = parts[0]

        # Normalize ID for lookup
        lookup_id = normalize_id(raw_id)

        # Update with title if found
        if lookup_id in id_to_title:
            updated_lines.append(f"{parts[0]} {id_to_title[lookup_id]}\n")
        else:
            updated_lines.append(line)

    # Write back
    with open(filename, "w") as fd:
        fd.writelines(updated_lines)
