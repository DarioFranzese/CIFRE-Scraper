from playwright.sync_api import sync_playwright

detail_url = "https://www.safran-group.com/jobs/france/reau/these-cifre-modelisation-thermo-hydraulique-roulements-fh-182736"

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
    
    page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    
    body_text = page.locator("body").inner_text()
    
    # Save the raw body text to check what is in there
    with open("scratch/safran_detail_body.txt", "w", encoding="utf-8") as f:
        f.write(body_text)
        
    print("Body text length:", len(body_text))
    # Let's print the first 2000 characters of the body text
    print(body_text[:2000])
    
    browser.close()
