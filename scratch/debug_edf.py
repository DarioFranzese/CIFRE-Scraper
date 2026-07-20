"""Debug script — inspect EDF page structure via Playwright."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from playwright.sync_api import sync_playwright

URL = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers?search[profil][34947]=34947"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    print(f"[debug] Navigating to {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    # Remove privacy overlays
    page.evaluate("""() => {
        const selectors = ['#privacy-container', '#privacy-overlay', '[class*="cookie"]', '[class*="privacy"]'];
        selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
    }""")

    # --- 1. Check the li.offer selector ---
    cards = page.locator("li.offer").all()
    print(f"\n[debug] li.offer count: {len(cards)}")

    # --- 2. Dump each card's outer HTML (first 2000 chars) ---
    for i, card in enumerate(cards):
        outer = card.evaluate("el => el.outerHTML")
        print(f"\n=== CARD {i} outerHTML (truncated) ===")
        print(outer[:2000])
        print("---")

    # --- 3. Check alternative selectors if li.offer is empty ---
    if len(cards) == 0:
        print("\n[debug] li.offer found nothing — trying alternatives...")
        for sel in [".offer", "li[class*='offer']", ".offers-list li",
                    "[class*='offer-item']", "[class*='job']", "article"]:
            count = page.locator(sel).count()
            if count:
                print(f"  Selector '{sel}' -> {count} matches")
                first_html = page.locator(sel).first.evaluate("el => el.outerHTML")
                print(f"  First match outerHTML: {first_html[:1000]}")

    # --- 4. Check link selectors inside each card ---
    if len(cards) > 0:
        card0 = cards[0]
        for link_sel in ["a.offer-link", "a[class*='offer']", "a[href*='offre']",
                         "a[href*='offer']", "a"]:
            count = card0.locator(link_sel).count()
            if count:
                href = card0.locator(link_sel).first.get_attribute("href")
                print(f"\n[debug] Card 0, link selector '{link_sel}' -> count={count}, href={href}")

    # --- 5. Dump full text of each card ---
    for i, card in enumerate(cards):
        text = card.inner_text(timeout=3000).strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        print(f"\n[debug] Card {i} text lines: {lines}")

    # --- 6. Check for pagination / load-more buttons ---
    for sel in ["[class*='pagination']", "[class*='load-more']", "[class*='pager']",
                "button[class*='more']", "a[class*='next']"]:
        count = page.locator(sel).count()
        if count:
            print(f"\n[debug] Pagination selector '{sel}' -> {count} matches")

    browser.close()
    print("\n[debug] Done.")
