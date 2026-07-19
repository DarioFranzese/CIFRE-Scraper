from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers?search[profil][34947]=34947"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating directly to {url}...")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    
    # Remove overlays
    page.evaluate("""() => {
        const selectors = ['#privacy-container', '#privacy-overlay', '[class*="cookie"]', '[class*="privacy"]'];
        selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
    }""")
    
    btn = page.locator("button[aria-label='Contract type']").first
    if btn.count():
        print("Contract type button text:", repr(btn.inner_text().strip()))
        
    # Find all offer cards. Let's see what card container selectors are actually on the page.
    # On EDF portal, individual job offers are typically '.offer-card' elements.
    cards = page.locator(".offer-card").all()
    print(f"\nFound {len(cards)} elements matching '.offer-card'")
    for i, card in enumerate(cards):
        try:
            print(f"  Card [{i}]:")
            lines = [l.strip() for l in card.inner_text().split("\n") if l.strip()]
            for j, line in enumerate(lines[:10]):
                print(f"    Line {j}: {repr(line)}")
        except Exception as e:
            print("Error parsing card:", e)
            
    browser.close()
