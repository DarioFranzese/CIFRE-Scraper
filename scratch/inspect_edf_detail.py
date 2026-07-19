from playwright.sync_api import sync_playwright

detail_url = "https://www.edf.fr/en/edf-join-us/offer/detail/FRA-REC-2026-27048"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating to {detail_url}...")
    page.goto(detail_url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    
    body_text = page.locator("body").inner_text()
    
    # Save detail body to check structure
    with open("scratch/edf_detail_body.txt", "w", encoding="utf-8") as f:
        f.write(body_text)
        
    print("Body text length:", len(body_text))
    # Look for common headers or markers
    terms = ["description", "mission", "profil", "contexte", "sujet", "responsabilités"]
    for t in terms:
        idx = body_text.lower().find(t.lower())
        if idx != -1:
            print(f"Found '{t}' at index {idx}. Snippet:")
            print(body_text[idx:idx+500])
            print("====================================")
            
    browser.close()
