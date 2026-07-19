import json
from scrapers.safran import SafranScraper

scraper = SafranScraper()
# We can also verify or modify the config object loaded in-memory if needed
print("Loaded Config Safran allowed tags:", scraper.config.get("safran", {}).get("allowed_tags"))

results = scraper.scrape()

print(f"\nFinal Scraped Results ({len(results)}):")
for i, res in enumerate(results):
    print(f"[{i}] Title: {res['title']}")
    print(f"    Link: {res['link']}")
    print(f"    Description length: {len(res['description'])}")
    print(f"    Description: {res['description'][:150]}...")
