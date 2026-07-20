"""Test the fixed Orange scraper."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__) + "/..")

from scrapers.orange import OrangeScraper

s = OrangeScraper()
results = s.scrape()
print(f"\n=== TOTAL OFFERS: {len(results)} ===")
for i, r in enumerate(results):
    print(f"\nOffer {i}:")
    print(f"  title: {r.get('title')}")
    print(f"  company: {r.get('company')}")
    print(f"  link: {r.get('link')}")
    desc = r.get('description', '')
    print(f"  description ({len(desc)} chars): {desc[:150]}...")
