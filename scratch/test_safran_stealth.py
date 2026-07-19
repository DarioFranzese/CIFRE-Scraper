from playwright.sync_api import sync_playwright

url = "https://www.safran-group.com/jobs?search=cifre"

def test_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        )
        page = context.new_page()
        page.add_init_script("delete navigator.__proto__.webdriver;")
        
        print(f"Navigating to {url}...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            cards = page.locator(".c-offer-item").all()
            print(f"Found {len(cards)} cards")
            for i, card in enumerate(cards):
                print(f"\n--- Card {i} ---")
                text = card.inner_text()
                print("Text lines:")
                for l in text.split("\n"):
                    print(f"  {repr(l)}")
                
                # Check link
                link_el = card.locator("a").first
                print("Link href:", link_el.get_attribute("href") if link_el.count() else "None")
        except Exception as e:
            print("Error:", e)
        finally:
            browser.close()

if __name__ == "__main__":
    test_playwright()
