from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers"

def test_browser(browser_type_name):
    print(f"\n--- Testing with {browser_type_name} ---")
    try:
        with sync_playwright() as p:
            browser_type = getattr(p, browser_type_name)
            browser = browser_type.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            title = page.title()
            print("Title:", title)
            
            # Check for buttons or if blocked
            buttons = page.locator("button").all()
            print(f"Found {len(buttons)} buttons")
            for i, btn in enumerate(buttons[:10]):
                try:
                    text = btn.inner_text().strip()
                    if text:
                        print(f"  [{i}] {repr(text)}")
                except Exception:
                    pass
            browser.close()
    except Exception as e:
        print("Error:", e)

test_browser("firefox")
test_browser("webkit")
