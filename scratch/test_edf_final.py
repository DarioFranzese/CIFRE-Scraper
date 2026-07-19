from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers?search[profil][34947]=34947"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    
    # Remove overlays
    page.evaluate("""() => {
        const selectors = ['#privacy-container', '#privacy-overlay', '[class*="cookie"]', '[class*="privacy"]'];
        selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
    }""")
    
    # Select li.offer
    cards = page.locator("li.offer").all()
    print(f"\nFound {len(cards)} offers:")
    
    for idx, card in enumerate(cards):
        try:
            # Find the anchor
            link_el = card.locator("a.offer-link").first
            if not link_el.count():
                link_el = card.locator("a").first
                
            href = link_el.get_attribute("href") or ""
            if href and not href.startswith("http"):
                href = f"https://www.edf.fr{href}"
                
            # Title is inside a.offer-link or header
            # Let's inspect the card inner text and title
            text = card.inner_text().strip()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            
            # The title is usually the main heading or the second line
            # Let's check:
            # line 0 is the date: "11 July 2026"
            # line 1 is the title: "Doctorant CIFRE - Ségregation..."
            title = lines[1] if len(lines) > 1 else lines[0]
            description = " ".join(lines[2:]) if len(lines) > 2 else text
            
            print(f"[{idx}] Title: {repr(title)}")
            print(f"    Link: {repr(href)}")
            print(f"    Description: {repr(description[:200])}")
        except Exception as e:
            print(f"[{idx}] Error: {e}")
            
    browser.close()
