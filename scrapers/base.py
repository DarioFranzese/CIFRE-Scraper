"""Abstract base class for all CIFRE PhD offer scrapers."""

import hashlib
import json
import os
from abc import ABC, abstractmethod
from datetime import date


def load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class BaseScraper(ABC):
    """Base class that every scraper must extend."""

    # Subclasses must set this to a short identifier, e.g. "orange", "thales"
    SOURCE_NAME: str = ""

    def __init__(self):
        self.config = load_config()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> list[dict]:
        """Run the scraper and return a list of normalised offer dicts.

        Each offer dict has:
            id          – deterministic hash for deduplication
            title       – job title
            company     – company name
            description – free text description / teaser
            link        – URL to the original posting
            source      – self.SOURCE_NAME
            date_found  – ISO date string (today)
        """
        raw_offers = self.scrape()
        normalised = []
        for offer in raw_offers:
            offer.setdefault("source", self.SOURCE_NAME)
            offer.setdefault("date_found", date.today().isoformat())
            offer["id"] = self._make_id(offer)
            normalised.append(offer)
        return normalised

    # ------------------------------------------------------------------
    # To be implemented by each subclass
    # ------------------------------------------------------------------

    @abstractmethod
    def scrape(self) -> list[dict]:
        """Return a list of raw offer dicts.

        Each dict MUST contain at least: title, company, description, link.
        The base class will fill in source, date_found and id automatically.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_id(offer: dict) -> str:
        """Create a deterministic id from source + link (or source + title + company)."""
        if offer.get("link"):
            raw = f"{offer['source']}::{offer['link']}"
        else:
            raw = f"{offer['source']}::{offer.get('title', '')}::{offer.get('company', '')}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _clean(text: str | None) -> str:
        """Strip and collapse whitespace."""
        if not text:
            return ""
        return " ".join(text.split())
