from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers"

with sync_playwright() as p:
    print("Launching headful browser...")
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    
    print("Page Title:", page.title())
    print("Page URL:", page.url())
    
    # Check if there is cookie banner
    try:
        accept_btn = page.locator("button:has-text('Accept'), button:has-text('Accepter')").first
        if accept_btn.is_visible(timeout=5000):
            accept_btn.click()
            print("Accepted cookies")
            page.wait_for_timeout(3000)
    except Exception as e:
        print("No cookie banner:", e)
        
    print("Page Title after cookie:", page.title())
    
    # List all buttons to see if the maintenance page is gone
    buttons = page.locator("button").all()
    print(f"Found {len(buttons)} buttons:")
    for i, btn in enumerate(buttons[:30]):
        try:
            text = btn.inner_text().strip()
            aria_label = btn.get_attribute("aria-label") or ""
            if text or aria_label:
                print(f"  [{i}] {repr(text)} | aria-label: {repr(aria_label)}")
        except Exception:
            pass
            
    # Save screenshot
    page.screenshot(path="scratch/edf_headful.png")
    browser.close()
