"""Scraping orchestrator — runs all scrapers and merges results into offers.json."""

import json
import os
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


def run_all_scrapers() -> dict:
    """Run every scraper, merge results, and return updated database.

    Returns a summary dict: {new: int, total: int, errors: list[str]}
    """
    db = load_offers()
    existing_ids = {o["id"] for o in db["offers"]}
    # Keep a map of id -> offer for quick lookup
    offers_map = {o["id"]: o for o in db["offers"]}

    new_count = 0
    errors = []

    for scraper_cls in ALL_SCRAPERS:
        scraper_name = scraper_cls.SOURCE_NAME
        print(f"\n{'='*60}")
        print(f"Running scraper: {scraper_name}")
        print(f"{'='*60}")
        try:
            scraper = scraper_cls()
            new_offers = scraper.run()
            for offer in new_offers:
                if offer["id"] not in existing_ids:
                    offer["status"] = "new"
                    offers_map[offer["id"]] = offer
                    existing_ids.add(offer["id"])
                    new_count += 1
                # If the offer already exists, keep its current status
        except Exception as e:
            error_msg = f"{scraper_name}: {e}"
            print(f"[ERROR] {error_msg}")
            errors.append(error_msg)

    # Rebuild offers list from map
    db["offers"] = list(offers_map.values())
    db["last_scrape"] = datetime.now().isoformat()

    # Mark previously "new" offers that haven't been actioned as "seen"
    # (We do NOT do this — keep them as "new" until the user acts on them)

    save_offers(db)

    summary = {
        "new": new_count,
        "total": len(db["offers"]),
        "errors": errors,
        "timestamp": db["last_scrape"],
    }
    print(f"\n{'='*60}")
    print(f"Scraping complete: {new_count} new offers, {len(db['offers'])} total")
    if errors:
        print(f"Errors: {errors}")
    print(f"{'='*60}")
    return summary


if __name__ == "__main__":
    run_all_scrapers()
