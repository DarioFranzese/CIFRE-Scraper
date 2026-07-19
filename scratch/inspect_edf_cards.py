from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers?search[profil][34947]=34947"

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    
    # Remove overlays
    page.evaluate("""() => {
        const selectors = ['#privacy-container', '#privacy-overlay', '[class*="cookie"]', '[class*="privacy"]'];
        selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
    }""")
    
    # Let's search for elements containing dates like "July 2026" or "18 July" or contract/location
    # and print their tag name, classes, and parent tags/classes
    elements = page.evaluate("""() => {
        // Let's find any text node or element containing "Permanent contract" or date patterns
        const results = [];
        const allEls = document.querySelectorAll('*');
        for (const el of allEls) {
            // Check if it is a container element that represents a card
            // Often a card is a div, article, or li with some class
            const text = el.textContent || '';
            if (el.className && typeof el.className === 'string' && el.className.includes('offer')) {
                results.push({
                    tagName: el.tagName,
                    class: el.className,
                    textSnippet: text.trim().substring(0, 100)
                });
            }
        }
        return results.slice(0, 50);
    }""")
    
    print("\nElements with 'offer' in class name:")
    for idx, item in enumerate(elements):
        print(f"  [{idx}] {item['tagName']}.{item['class']} -> {repr(item['textSnippet'])}")
        
    # Let's do a search for any anchor tags on the page that point to an offer detail
    links = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href') || '';
            if (href.includes('/offre') || href.includes('/job')) {
                results.push({
                    text: a.textContent.trim(),
                    href: href,
                    parentClass: a.parentElement ? a.parentElement.className : ''
                });
            }
        });
        return results;
    }""")
    print("\nJob links found on page:")
    for idx, l in enumerate(links):
        print(f"  [{idx}] Text: {repr(l['text'])} | Href: {repr(l['href'])} | ParentClass: {repr(l['parentClass'])}")
        
    browser.close()
