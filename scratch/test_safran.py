from playwright.sync_api import sync_playwright

url = "https://www.safran-group.com/jobs?search=cifre"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    
    print("Page Title:", page.title())
    print("Page URL:", page.url())
    
    # Save screenshot and html
    page.screenshot(path="scratch/safran_landing.png")
    with open("scratch/safran_landing.html", "w", encoding="utf-8") as f:
        f.write(page.content())
        
    browser.close()
