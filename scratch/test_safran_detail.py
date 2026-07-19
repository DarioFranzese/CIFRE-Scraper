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
    
    print(f"Navigating to {detail_url}...")
    try:
        page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        print("Page Title:", page.title())
        
        # Save html
        content = page.content()
        print("Content length:", len(content))
        
        # Try to find description element
        # Common selectors: .c-job-description, .job-description, .job-details, main, etc.
        body_text = page.locator("body").inner_text()
        print("Body text snippet (first 1000 chars):")
        print(body_text[:1000])
    except Exception as e:
        print("Error:", e)
    finally:
        browser.close()
