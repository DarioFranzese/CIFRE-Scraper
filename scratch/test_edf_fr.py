from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/edf-recrute/rejoignez-nous/voir-les-offres/nos-offres"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    )
    page = context.new_page()
    page.add_init_script("delete navigator.__proto__.webdriver;")
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    
    print("Page Title before accept:", page.title())
    
    try:
        accept_btn = page.locator("button:has-text('Accept'), button:has-text('Accepter')").first
        if accept_btn.is_visible(timeout=5000):
            accept_btn.click()
            print("Clicked Accept button.")
            page.wait_for_timeout(5000)
    except Exception as e:
        print("Could not click accept button:", e)
        
    print("Page Title after accept:", page.title())
    
    # List all buttons
    buttons = page.locator("button").all()
    print(f"Found {len(buttons)} buttons after accept:")
    for i, btn in enumerate(buttons):
        try:
            text = btn.inner_text().strip()
            aria_label = btn.get_attribute("aria-label") or ""
            class_name = btn.get_attribute("class") or ""
            if text or aria_label:
                print(f"  [{i}] Text: {repr(text)} | aria-label: {repr(aria_label)} | class: {repr(class_name)}")
        except Exception:
            pass
            
    # Take a screenshot to inspect
    page.screenshot(path="scratch/edf_fr_after_accept.png")
    
    browser.close()
