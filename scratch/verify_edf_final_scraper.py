import json
from scrapers.edf import EDFScraper

scraper = EDFScraper()
print("Initialized EDFScraper. Running scrape...")
results = scraper.run()

print(f"\nFinal Scraped Results ({len(results)}):")
for i, res in enumerate(results):
    print(f"[{i}] Title: {res['title']}")
    print(f"    Link: {res['link']}")
    print(f"    Description length: {len(res['description'])}")
    print(f"    Description: {res['description'][:150]}...")
