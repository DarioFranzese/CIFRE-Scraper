from playwright.sync_api import sync_playwright

url = "https://www.edf.fr/edf-recrute/rejoignez-nous/voir-les-offres/nos-offres"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(3000)
    with open("scratch/edf_maintenance.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    browser.close()
