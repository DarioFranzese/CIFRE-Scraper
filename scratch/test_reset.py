from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.abg.asso.fr/fr/candidatOffres', wait_until='networkidle')
    
    kw = page.locator('input[name="criteria[mot_cle]"]')
    kw.fill('CIFRE')
    print('Filled CIFRE. Value before click:', kw.input_value())
    
    # Click reset button
    page.locator('#monBoutonReset').click()
    page.wait_for_timeout(3000)
    
    print('Value after click:', kw.input_value())
    items = page.locator('.item.it_offre')
    print('Items count after clicking monBoutonReset:', items.count())
    
    browser.close()
