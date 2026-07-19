from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    
    # Cookie accept
    try:
        accept_btn = page.locator("button:has-text('Accept'), button:has-text('Accepter')").first
        if accept_btn.is_visible(timeout=5000):
            accept_btn.click()
            print("Cookie accepted")
            page.wait_for_timeout(3000)
    except Exception as e:
        print("No cookie banner:", e)
        
    # Print all button elements to find the correct filters
    buttons = page.locator("button").all()
    print(f"\nFound {len(buttons)} buttons:")
    for i, btn in enumerate(buttons):
        try:
            text = btn.inner_text().strip()
            aria_label = btn.get_attribute("aria-label") or ""
            class_name = btn.get_attribute("class") or ""
            if text or aria_label:
                print(f"  [{i}] Text: {repr(text)} | aria-label: {repr(aria_label)} | class: {repr(class_name)}")
        except Exception:
            pass
            
    # Try to find the button with aria-label="Contract type" or containing "Thesis"
    btn_target = page.locator("button[aria-label='Contract type']").first
    if btn_target.count():
        print("\nFound Contract type button. Click it to expand...")
        btn_target.click()
        page.wait_for_timeout(2000)
        
        # Now let's list all inputs/checkboxes or labels to select "Thesis"
        labels = page.locator("label").all()
        print(f"\nFound {len(labels)} labels after expanding:")
        for i, lbl in enumerate(labels):
            try:
                text = lbl.inner_text().strip()
                if text:
                    print(f"  Label [{i}] Text: {repr(text)}")
                    if "thesis" in text.lower():
                        print("    -> FOUND THESIS! Clicking the label...")
                        lbl.click()
                        page.wait_for_timeout(5000) # wait for page to update
            except Exception:
                pass
                
    # Now let's list the job offers visible on the page
    cards = page.locator(".offer-card, .job-card, [class*='offer'], article").all()
    print(f"\nFound {len(cards)} card elements on the filtered page:")
    for i, card in enumerate(cards):
        try:
            txt = card.inner_text().replace('\n', ' ')[:200]
            print(f"  Offer [{i}]: {txt}")
        except Exception:
            pass
            
    page.screenshot(path="scratch/edf_webkit_results.png")
    browser.close()
