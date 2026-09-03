"""Test suite for Association Bernard Gregory (ABG) scraper.

Tests:
1. CIFRE keyword search and detailed offer extraction (title, company, description, link).
2. Empty keyword search verifying multi-page AJAX pagination via '.resultats.clearfix' and '.pager_suiv a'.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from scrapers.abg import ABGScraper


class TestABGScraper(unittest.TestCase):

    def test_01_cifre_search_and_detail_extraction(self):
        """Verify that searching for 'CIFRE' returns valid offers with all required fields."""
        print("\n[TEST 1] Running CIFRE search with ABGScraper...")
        scraper = ABGScraper()
        # Ensure keyword is CIFRE
        scraper.config["abg"] = {"keyword": "CIFRE", "max_pages": 5}
        offers = scraper.run()

        print(f"[TEST 1] Retrieved {len(offers)} offers")
        self.assertGreater(len(offers), 0, "Should find at least 1 CIFRE offer on ABG")

        for idx, offer in enumerate(offers):
            print(f"\n--- Offer {idx + 1} ---")
            print(f"ID:          {offer.get('id')}")
            print(f"Title:       {offer.get('title')}")
            print(f"Company:     {offer.get('company')}")
            print(f"Link:        {offer.get('link')}")
            print(f"Description: {offer.get('description', '')[:120]}... (length: {len(offer.get('description', ''))})")
            print(f"Source:      {offer.get('source')}")
            print(f"Date found:  {offer.get('date_found')}")

            # Assert required schema fields
            self.assertTrue(offer.get("id"), "Offer ID must be present")
            self.assertTrue(offer.get("title"), "Offer Title must be present")
            self.assertTrue(offer.get("company"), "Offer Company must be present")
            self.assertTrue(offer.get("link"), "Offer Link must be present")
            self.assertTrue(offer.get("link").startswith("http"), "Offer Link must be an absolute URL")
            self.assertTrue(offer.get("description"), "Offer Description must be present")
            self.assertEqual(offer.get("source"), "abg", "Offer source must be 'abg'")

        print("\n[TEST 1] PASSED: All CIFRE offers extracted and validated.")

    def test_02_empty_keyword_ajax_pagination(self):
        """Verify that searching without keyword triggers multi-page AJAX pagination on .resultats.clearfix."""
        print("\n[TEST 2] Testing empty keyword AJAX pagination on .resultats.clearfix...")
        scraper = ABGScraper()
        # Request up to 3 pages without keyword
        cards = scraper._fetch_cards_with_playwright(keyword="", max_pages=3)

        print(f"[TEST 2] Total cards collected across pages: {len(cards)}")
        self.assertGreaterEqual(
            len(cards), 20,
            "Paginating across at least 2-3 pages should collect >= 20 cards (10 per page)"
        )

        unique_links = set(c["link"] for c in cards)
        self.assertEqual(
            len(unique_links), len(cards),
            "All paginated cards should have unique URLs"
        )

        print("\n[TEST 2] PASSED: Multi-page AJAX pagination successfully traversed.")


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestABGScraper("test_01_cifre_search_and_detail_extraction"))
    suite.addTest(TestABGScraper("test_02_empty_keyword_ajax_pagination"))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
