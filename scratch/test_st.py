import re
from playwright.sync_api import sync_playwright

url = "https://stmicroelectronics.eightfold.ai/careers?query=CIFRE&location=France&pid=563637171228634&domain=stmicroelectronics.com&sort_by=relevance"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector(".card.position-card", timeout=30000)
    
    # 1. Click show more until exhausted
    show_more = page.locator(".btn.btn-sm.btn-secondary.show-more-positions")
    while show_more.count() > 0 and show_more.is_visible():
        show_more.first.click()
        page.wait_for_timeout(2000)
        show_more = page.locator(".btn.btn-sm.btn-secondary.show-more-positions")
        
    cards = page.locator(".card.position-card")
    count = cards.count()
    print(f"Found {count} cards in total")
    
    seen_titles = set()
    offers = []
    
    for i in range(count):
        card = cards.nth(i)
        card_text = card.inner_text().strip()
        lines = [line.strip() for line in card_text.split("\n") if line.strip()]
        title = lines[0] if lines else ""
        
        # Only CIFRE offers and deduplicate by title
        if "cifre" not in title.lower():
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        # Click card via dispatch_event or scroll
        card.scroll_into_view_if_needed()
        card.dispatch_event("click")
        page.wait_for_timeout(1000)
        
        page.wait_for_selector(".position-container .position-job-description", timeout=10000)
        
        current_url = page.url
        desc_html = page.locator(".position-job-description").first.inner_html()
        
        m = re.search(r"pid=(\d+)", current_url)
        pid = m.group(1) if m else "unknown"
        
        offers.append({
            "title": title,
            "company": "STMicroelectronics",
            "link": current_url,
            "desc_len": len(desc_html),
            "pid": pid,
        })
        print(f"[{len(offers)}] {title[:65]} | PID: {pid} | Desc len: {len(desc_html)}")

    print(f"\nTotal scraped offers: {len(offers)}")
    browser.close()
