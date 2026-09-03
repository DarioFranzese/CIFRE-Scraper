"""Scraping orchestrator — runs all scrapers and merges results into offers.json."""

import json
import os
import re
import unicodedata
from datetime import datetime

from scrapers import ALL_SCRAPERS


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OFFERS_FILE = os.path.join(DATA_DIR, "offers.json")


def load_offers() -> dict:
    """Load the current offers database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(OFFERS_FILE):
        with open(OFFERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_scrape": None, "offers": []}


def save_offers(db: dict) -> None:
    """Save the offers database to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OFFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, stripping accents, punctuation, and extra whitespace."""
    if not text:
        return ""
    # Normalize unicode (decompose accents: é -> e, etc.)
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # Remove gender indicators like (h/f), (f/h), (m/f), f/m, h/m, f-m, etc.
    text = re.sub(r"\b(h/f|f/h|m/f|f/m|h/m|f\s*-\s*m|h\s*-\s*f|m\s*-\s*f|f\s*-\s*h)\b", " ", text)
    # Remove non-alphanumeric chars
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def are_offers_duplicate(o1: dict, o2: dict) -> bool:
    """Check if two offers are duplicates across same or different providers.

    Matches if:
    1. Exact ID match (same source + link/hash)
    2. Identical normalized title AND compatible company names
    3. Identical normalized title with specific length (>= 30 chars or >= 4 words)
       where company names don't directly contradict each other
    """
    if o1.get("id") and o2.get("id") and o1["id"] == o2["id"]:
        return True

    t1 = normalize_text(o1.get("title", ""))
    t2 = normalize_text(o2.get("title", ""))
    if not t1 or not t2:
        return False

    if t1 == t2:
        c1 = normalize_text(o1.get("company", ""))
        c2 = normalize_text(o2.get("company", ""))

        # Compatible companies (one unknown/empty, or one contains the other)
        if not c1 or not c2 or c1 == "unknown" or c2 == "unknown" or c1 in c2 or c2 in c1:
            return True

        # Highly specific thesis title (e.g. >= 30 chars or >= 4 words)
        if len(t1) >= 30 or len(t1.split()) >= 4:
            return True

    return False


def run_all_scrapers() -> dict:
    """Run every scraper, filter duplicates, purge expired offers, and return summary.

    - De-duplicates offers across providers matching by title/company.
    - Preserves user status (e.g. applied, not_interested, seen) and original date_found.
    - Removes offers from the database that were not found in the latest scrape.
    - Protects existing offers from a provider if that provider's scraper failed.

    Returns a summary dict: {new: int, total: int, removed: int, errors: list[str], timestamp: str}
    """
    old_db = load_offers()
    old_offers = old_db.get("offers", [])

    # Transition previous "new" offers to "seen" so that ONLY offers
    # discovered for the first time during THIS scrape run get status "new"
    for offer in old_offers:
        if offer.get("status") == "new":
            offer["status"] = "seen"

    current_offers = []
    successful_sources = set()
    errors = []
    new_count = 0

    for scraper_cls in ALL_SCRAPERS:
        scraper_name = scraper_cls.SOURCE_NAME
        print(f"\n{'='*60}")
        print(f"Running scraper: {scraper_name}")
        print(f"{'='*60}")
        try:
            scraper = scraper_cls()
            scraped = scraper.run()
            successful_sources.add(scraper_name)

            for offer in scraped:
                # 1. Check for duplicate against offers ALREADY accepted in this run
                is_duplicate = False
                for existing in current_offers:
                    if are_offers_duplicate(offer, existing):
                        is_duplicate = True
                        break

                if is_duplicate:
                    # Skip duplicate from another/same provider
                    continue

                # 2. Check if this offer existed in old_offers to preserve status/date_found
                old_match = None
                for prev in old_offers:
                    if are_offers_duplicate(offer, prev):
                        old_match = prev
                        break

                if old_match:
                    # Preserve previous user tracking status and original discovery date
                    offer["status"] = old_match.get("status", "seen")
                    offer["date_found"] = old_match.get("date_found", offer.get("date_found"))
                else:
                    # Brand new offer
                    offer["status"] = "new"
                    new_count += 1

                current_offers.append(offer)

        except Exception as e:
            error_msg = f"{scraper_name}: {e}"
            print(f"[ERROR] {error_msg}")
            errors.append(error_msg)

    # If any scraper failed, preserve previous offers from that specific source
    # so a temporary network glitch does not purge all offers from that provider
    failed_sources = set(s.SOURCE_NAME for s in ALL_SCRAPERS) - successful_sources
    if failed_sources:
        print(f"[WARNING] Preserving existing offers for failed scrapers: {failed_sources}")
        for prev in old_offers:
            if prev.get("source") in failed_sources:
                if not any(are_offers_duplicate(prev, o) for o in current_offers):
                    current_offers.append(prev)

    # Number of offers removed from database
    removed_count = max(0, len(old_offers) + new_count - len(current_offers))

    db = {
        "offers": current_offers,
        "last_scrape": datetime.now().isoformat(),
    }
    save_offers(db)

    summary = {
        "new": new_count,
        "total": len(current_offers),
        "removed": removed_count,
        "errors": errors,
        "timestamp": db["last_scrape"],
    }
    print(f"\n{'='*60}")
    print(f"Scraping complete: {new_count} new, {removed_count} removed, {len(current_offers)} total")
    if errors:
        print(f"Errors: {errors}")
    print(f"{'='*60}")
    return summary


if __name__ == "__main__":
    run_all_scrapers()
