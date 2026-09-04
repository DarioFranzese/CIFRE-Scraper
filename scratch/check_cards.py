from playwright.sync_api import sync_playwright

url = "https://stmicroelectronics.eightfold.ai/careers?query=CIFRE&location=France&pid=563637171228634&domain=stmicroelectronics.com&sort_by=relevance"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector(".card.position-card", timeout=30000)
    
    show_more = page.locator(".btn.btn-sm.btn-secondary.show-more-positions")
    click_count = 0
    while show_more.count() > 0 and show_more.is_visible():
        click_count += 1
        print(f"Click #{click_count}")
        show_more.first.click()
        page.wait_for_timeout(2500)
        show_more = page.locator(".btn.btn-sm.btn-secondary.show-more-positions")
        
    cards = page.locator(".card.position-card")
    print("Total cards:", cards.count())
    for i in range(cards.count()):
        c = cards.nth(i)
        t = c.inner_text().split("\n")[0].strip()
        cls = c.get_attribute("class")
        print(f'{i:2d} | class="{cls}" | {t}')
    browser.close()
