"""Base classes and common utilities for library parsers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup


class LibraryParser(ABC):
    """Abstract base class for library parsers."""

    name: str = "unknown"
    url_template: str = ""

    @classmethod
    @abstractmethod
    def matches(cls, ident: str) -> bool:
        """Check if this parser can handle the given ID."""
        pass

    @classmethod
    @abstractmethod
    def normalize_id(cls, raw_id: str) -> str:
        """Normalize a raw ID from input file to canonical form."""
        pass

    @classmethod
    def fetch_page(cls, ident: str) -> BeautifulSoup:
        """Fetch and parse the library page for the given ID."""
        url = cls.url_template.format(id=ident)
        ret = requests.get(url)
        return BeautifulSoup(ret.text, features="html.parser")

    @classmethod
    @abstractmethod
    def parse(cls, ident: str) -> Dict[str, Any]:
        """Parse the library entry for the given ID."""
        pass

    @classmethod
    def create_entry(cls, ident: str) -> Dict[str, Any]:
        """Create a base entry dict with common fields."""
        return {
            "id": ident,
            "library": cls.name,
            "status": [],
        }


def determine_availability(available_text: str, unavailable_keywords: List[str]) -> bool:
    """Determine if an item can be borrowed based on availability text."""
    for keyword in unavailable_keywords:
        if keyword.lower() in available_text.lower():
            return False
    return True
