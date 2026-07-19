import json
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://www.safran-group.com/jobs?search=cifre"

def get_detail_page_content(url):
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
        
        print(f"Navigating to detail in fresh browser: {url}...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            body_text = page.locator("body").inner_text()
            print("Length of body text:", len(body_text))
            
            desc_start = body_text.find("Job Description")
            if desc_start == -1:
                desc_start = body_text.find("Description du poste")
            if desc_start == -1:
                desc_start = body_text.find("Description de la mission")
            print("desc_start index:", desc_start)
        except Exception as e:
            print("Error:", e)
        finally:
            browser.close()

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
    
    print(f"Navigating to search page: {SEARCH_URL}...")
    page.goto(SEARCH_URL, wait_until="networkidle")
    page.wait_for_timeout(5000)
    
    cards = page.locator("div.c-offer-item").all()
    print(f"Found {len(cards)} cards")
    links = []
    for card in cards:
        link_el = card.locator("a").first
        href = link_el.get_attribute("href") if link_el.count() else ""
        if href and not href.startswith("http"):
            href = f"https://www.safran-group.com{href}"
        links.append(href)
    browser.close()

if links:
    get_detail_page_content(links[0])
