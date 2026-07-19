from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # Remove privacy / cookie overlays from DOM
    page.evaluate("""() => {
        const selectors = [
            '#privacy-container', '#privacy-overlay', '#tarteaucitronRoot',
            '[id*="cookie"]', '[class*="cookie"]', '[class*="privacy"]'
        ];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });
        document.body.classList.remove('tc-modal-open');
        document.body.style.overflow = 'auto';
    }""")
    print("Overlays removed.")
    page.wait_for_timeout(2000)
    
    # Click "Contract type"
    btn = page.locator("button[aria-label='Contract type']").first
    btn.click()
    page.wait_for_timeout(2000)
    
    # Get HTML of elements around Thesis
    html = page.evaluate("""() => {
        const el = Array.from(document.querySelectorAll('label, span, input, button')).find(x => x.textContent.trim() === 'Thesis');
        return el ? el.outerHTML : 'Not found';
    }""")
    print("Thesis element HTML:")
    print(html)
    
    parent_html = page.evaluate("""() => {
        const el = Array.from(document.querySelectorAll('label, span, input, button')).find(x => x.textContent.trim() === 'Thesis');
        return el && el.parentElement ? el.parentElement.outerHTML : 'No parent';
    }""")
    print("\nParent Element HTML:")
    print(parent_html)
    
    browser.close()
