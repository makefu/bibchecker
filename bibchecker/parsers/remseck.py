"""Parser for Mediathek Remseck."""
from typing import Dict, Any, List

from bibchecker.base import LibraryParser


class RemseckParser(LibraryParser):
    """Parser for Mediathek Remseck (Koha-based)."""

    name = "remseck"
    url_template = "https://mt-remseck.lmscloud.net/cgi-bin/koha/opac-detail.pl?biblionumber={id}"

    # Keywords indicating item cannot be borrowed
    UNAVAILABLE_KEYWORDS = [
        "ausgeliehen",
        "checkedout",
    ]

    @classmethod
    def matches(cls, ident: str) -> bool:
        """Check if this parser can handle the given ID (numeric only)."""
        return ident.strip().isdigit()

    @classmethod
    def normalize_id(cls, raw_id: str) -> str:
        """Normalize a raw ID from input file to canonical form."""
        return raw_id.strip()

    @classmethod
    def parse(cls, ident: str) -> Dict[str, Any]:
        """Parse Remseck library entry."""
        entry = cls.create_entry(ident)
        data = cls.fetch_page(ident)

        # Parse title
        cls._parse_title(data, entry)

        # Parse holdings
        entry["status"] = cls._parse_holdings(data)

        return entry

    @classmethod
    def _parse_title(cls, data: Any, entry: Dict[str, Any]) -> None:
        """Parse title from the page."""
        title_elem = data.find("h1", {"class": "title"})
        if title_elem:
            title_text = title_elem.get_text(separator=" ", strip=True)
            if " / " in title_text:
                entry["Titel"], entry["TitelExtra"] = title_text.split(" / ", 1)
            else:
                entry["Titel"] = title_text

    @classmethod
    def _parse_holdings(cls, data: Any) -> List[Dict[str, Any]]:
        """Parse holdings table."""
        holdings: List[Dict[str, Any]] = []
        holdings_table = data.find("table", {"id": "holdingst"})
        if not holdings_table:
            return holdings

        tbody = holdings_table.find("tbody")
        if not tbody:
            return holdings

        for row in tbody.find_all("tr"):
            item = cls._parse_holding_row(row)
            if item:
                holdings.append(item)

        return holdings

    @classmethod
    def _parse_holding_row(cls, row: Any) -> Dict[str, Any]:
        """Parse a single holding row."""
        item: Dict[str, Any] = {}

        # Get library/location
        loc_cell = row.find("td", {"class": "location"})
        if loc_cell:
            lib_link = loc_cell.find("a", {"class": "library_info"})
            if lib_link:
                bib_text = lib_link.get_text(strip=True).replace("\n", " ").strip()
                # Remove info icon if present
                if bib_text.startswith("ⓘ"):
                    bib_text = bib_text[1:].strip()
                item["bib"] = bib_text

            shelf = loc_cell.find("span", {"class": "shelvingloc"})
            if shelf:
                item["standort"] = shelf.get_text(strip=True)

        # Get call number/signature
        callno_cell = row.find("td", {"class": "call_no"})
        if callno_cell:
            sig_text = callno_cell.get_text(strip=True).split("(")[0].strip()
            item["sig"] = sig_text

        # Get status
        status_cell = row.find("td", {"class": "status"})
        if status_cell:
            status_span = status_cell.find("span", {"class": "item-status"})
            if status_span:
                item["available"] = status_span.get_text(strip=True)
            else:
                instock = status_cell.find("link", {"href": "http://schema.org/InStock"})
                item["available"] = "Verfügbar" if instock else "Unbekannt"

        # Get due date
        duedate_cell = row.find("td", {"class": "date_due"})
        if duedate_cell:
            duedate = duedate_cell.get_text(strip=True)
            if duedate and item.get("available"):
                item["available"] = f"{item['available']} - Fällig am: {duedate}"

        # Determine borrowability
        avail_text = item.get("available", "")
        item["can_be_borrowed"] = not any(
            kw in avail_text.lower() for kw in cls.UNAVAILABLE_KEYWORDS
        ) and "OutOfStock" not in str(status_cell)

        return item
