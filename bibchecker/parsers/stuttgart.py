"""Parser for Stadtbibliothek Stuttgart."""
from typing import Dict, Any, List

from bibchecker.base import LibraryParser, determine_availability


class StuttgartParser(LibraryParser):
    """Parser for Stadtbibliothek Stuttgart."""

    name = "stuttgart"
    url_template = "https://stadtbibliothek-stuttgart.de/aDISWeb/app?service=direct%2F0%2FHome%2F%24DirectLink&sp=SOPAC&sp={id}"

    # Keywords indicating item cannot be borrowed
    UNAVAILABLE_KEYWORDS = [
        "Ausgeliehen",
        "Ist nur vor Ort nutzbar",
        "Nicht im Regal",
        "noch nicht im Haus",
        "Reserviert",
        "zur Zeit vermisst",
    ]

    # Mapping from German column headers to internal keys
    COLUMN_MAPPING = {
        "Bibliothek": "bib",
        "Standort": "standort",
        "Signatur": "sig",
        "Bestellmöglichkeit": "method",
        "Verfügbarkeit": "available",
        "Reservierung": "reservation",
    }

    @classmethod
    def matches(cls, ident: str) -> bool:
        """Check if this parser can handle the given ID."""
        upper = ident.upper()
        return upper.startswith("SAK") or upper.startswith("AK")

    @classmethod
    def normalize_id(cls, raw_id: str) -> str:
        """Normalize a raw ID from input file to canonical form."""
        upper = raw_id.upper().strip()
        if upper.startswith("AK"):
            return f"S{upper}"
        if upper.startswith("JAVASCRIPT:HTMLONLINK"):
            return raw_id.split("'")[1]
        return upper

    @classmethod
    def parse(cls, ident: str) -> Dict[str, Any]:
        """Parse Stuttgart library entry."""
        entry = cls.create_entry(ident)
        data = cls.fetch_page(ident)

        # Parse metadata from info table
        cls._parse_metadata(data, entry)

        # Parse availability from holdings table
        entry["status"] = cls._parse_holdings(data)

        return entry

    @classmethod
    def _parse_metadata(cls, data: Any, entry: Dict[str, Any]) -> None:
        """Parse metadata (title, etc.) from the info table."""
        tab = data.find("table", {"class": "gi"})
        if tab is None:
            return

        for row in tab.find_all("tr"):
            try:
                right_elem = row.find("td", {"class": "spalterechts"})
                left_elem = row.find("th")
                if right_elem is None or left_elem is None:
                    continue

                right = right_elem.get_text().strip()
                left = left_elem.get_text().strip()

                if left.startswith("Titel"):
                    left = "Titel"
                    try:
                        entry["Titel"], entry["TitelExtra"] = right.replace("Titel ", "").split(" / ")
                    except ValueError:
                        entry["Titel"] = right
                elif left:
                    entry[left] = right
            except Exception:
                pass

    @classmethod
    def _parse_holdings(cls, data: Any) -> List[Dict[str, Any]]:
        """Parse holdings/availability table."""
        holdings: List[Dict[str, Any]] = []
        tab = data.find("table", {"class": "rTable_table"})
        if tab is None:
            return holdings

        thead = tab.find("thead")
        tbody = tab.find("tbody")
        if thead is None or tbody is None:
            return holdings

        # Build column mapping from header
        available_rows: List[str] = []
        for row in thead.find_all("th"):
            row_text = row.get_text().strip()
            available_rows.append(cls.COLUMN_MAPPING.get(row_text, row_text))

        # Parse each row
        for row in tbody.find_all("tr"):
            item: Dict[str, Any] = {}
            for idx, col in enumerate(row.find_all("td")):
                if idx < len(available_rows):
                    item[available_rows[idx]] = col.get_text().strip()

            available = item.get("available", "")
            item["can_be_borrowed"] = determine_availability(available, cls.UNAVAILABLE_KEYWORDS)
            holdings.append(item)

        return holdings
