import json
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://www.safran-group.com/jobs?search=cifre"
ALLOWED_TAGS = ["IT", "Mathematics and algorithms", "Data", "Architecture and systems engineering"]

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
    page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    
    card_selector = "div.c-offer-item"
    cards = page.locator(card_selector).all()
    print(f"[safran] Found {len(cards)} raw cards on page")
    
    offers = []
    for idx, card in enumerate(cards):
        try:
            card_text = card.inner_text()
            lines = [l.strip() for l in card_text.split("\n") if l.strip()]
            if not lines:
                continue
            
            title = lines[0]
            tags = [line for line in lines if len(line) < 60]
            last_tag = tags[-1] if tags else ""
            
            tag_ok = False
            if last_tag:
                if any(allowed.lower() in last_tag.lower() for allowed in ALLOWED_TAGS):
                    tag_ok = True
            else:
                tag_ok = True
                
            link_el = card.locator("a").first
            href = link_el.get_attribute("href") if link_el.count() else ""
            if href and not href.startswith("http"):
                href = f"https://www.safran-group.com{href}"
                
            offers.append({
                "title": title,
                "last_tag": last_tag,
                "tag_ok": tag_ok,
                "link": href
            })
        except Exception as e:
            print(f"Error parsing raw card {idx}: {e}")
            
    # Now let's visit detail pages
    for o in offers:
        if not o["link"]:
            continue
        print(f"\nFetching detail: {o['link']}...")
        try:
            detail_page = context.new_page()
            detail_page.goto(o["link"], wait_until="domcontentloaded", timeout=60000)
            detail_page.wait_for_timeout(5000) # Let's wait 5s to be absolutely sure it loaded
            
            body_text = detail_page.locator("body").inner_text()
            
            desc_start = body_text.find("Job Description")
            if desc_start == -1:
                desc_start = body_text.find("Description du poste")
            if desc_start == -1:
                desc_start = body_text.find("Description de la mission")
                
            print(f"  desc_start index: {desc_start}")
            
            description = ""
            if desc_start != -1:
                description = body_text[desc_start:].strip()
                company_idx = description.find("Company Information")
                print(f"  company_idx index: {company_idx}")
                if company_idx != -1:
                    description = description[:company_idx].strip()
                else:
                    locate_idx = description.find("Locate your future workplace")
                    print(f"  locate_idx index: {locate_idx}")
                    if locate_idx != -1:
                        description = description[:locate_idx].strip()
                        
            print(f"  Extracted description (length {len(description)}):")
            if description:
                print(f"  Snippet: {description[:200].replace(chr(10), ' ')}...")
            detail_page.close()
        except Exception as e:
            print(f"  Error loading detail page: {e}")
            
    browser.close()
