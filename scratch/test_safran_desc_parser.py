from playwright.sync_api import sync_playwright

detail_url = "https://www.safran-group.com/jobs/france/colombes/these-cifre-surveillance-vibratoire-techniques-separation-sources-systeme-rgb-fh-176532"

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
    
    idx = body_text.lower().find("job description")
    if idx != -1:
        desc_text = body_text[idx:]
        with open("scratch/safran_desc.txt", "w", encoding="utf-8") as f:
            f.write(desc_text)
        print("Successfully wrote description to scratch/safran_desc.txt")
        
    browser.close()
