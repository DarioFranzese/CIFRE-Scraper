from playwright.sync_api import sync_playwright

url = "https://stmicroelectronics.eightfold.ai/careers?query=CIFRE&location=France&pid=563637171228634&domain=stmicroelectronics.com&sort_by=relevance"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector(".position-container .position-job-description", timeout=30000)
    
    res = page.evaluate("""() => {
        const desc = document.querySelector('.position-job-description');
        if (!desc) return null;
        
        function summarize(el, depth=0) {
            return {
                tag: el.tagName,
                className: el.className,
                childrenCount: el.children.length,
                innerTextLen: el.innerText ? el.innerText.length : 0,
                sample: el.innerText ? el.innerText.substring(0, 80).replace(/\\s+/g, ' ') : '',
                children: depth < 2 ? Array.from(el.children).map(c => summarize(c, depth+1)) : []
            };
        }
        return summarize(desc);
    }""")
    
    import pprint
    pprint.pprint(res)
    browser.close()
