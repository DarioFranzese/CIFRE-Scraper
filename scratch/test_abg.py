import time
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to https://www.abg.asso.fr/fr/candidatOffres ...")
        page.goto("https://www.abg.asso.fr/fr/candidatOffres", wait_until="networkidle")
        print("Page title:", page.title())

        # Check keyword input
        kw = page.locator('input[name="criteria[mot_cle]"]')
        print("Keyword input count:", kw.count(), "visible:", kw.is_visible())

        # Check monBoutonReset
        reset_btn = page.locator("#monBoutonReset")
        print("Reset btn count:", reset_btn.count(), "visible:", reset_btn.is_visible())

        # Check monBoutonSubmit
        submit_btn = page.locator("#monBoutonSubmit")
        print("Submit btn count:", submit_btn.count(), "visible:", submit_btn.is_visible())

        # Let's type CIFRE and submit
        kw.fill("CIFRE")
        # How to trigger search?
        # User says: "sotto l' oggetto di tipo input name=\"criteria[mot_cle]\" devi inserire la parola \"CIFRE\" ed avviare lo script di ricerca (id=\"monBoutonReset\" title =\"Reinitialiser\")."
        # Let's see what happens if we submit or evaluate
        print("Triggering search with monBoutonSubmit...")
        submit_btn.evaluate("el => el.click()")
        page.wait_for_timeout(3000)

        # Check items
        items = page.locator(".item.it_offre")
        print("Items found with CIFRE:", items.count())
        for i in range(items.count()):
            it = items.nth(i)
            title_logo = it.locator(".titre_logo a")
            print(f"Offer {i+1}:", title_logo.inner_text(), "->", title_logo.get_attribute("href"))

        # Check pagination
        res_pag = page.locator(".resultats.clearfix")
        print("Pagination wrapper count:", res_pag.count())

        # Now test search WITHOUT keyword to check multi-page pagination
        print("\n--- Testing empty keyword search (pagination test) ---")
        kw.fill("")
        submit_btn.evaluate("el => el.click()")
        page.wait_for_timeout(3000)

        items_all = page.locator(".item.it_offre")
        print("Items without keyword:", items_all.count())

        res_pag = page.locator(".resultats.clearfix")
        print("Pagination count:", res_pag.count())
        if res_pag.count() > 0:
            next_link = page.locator(".resultats.clearfix .pager_suiv a").first
            print("Next page link exists:", next_link.count(), "visible:", next_link.is_visible())
            if next_link.count() > 0:
                print("Clicking next page...")
                next_link.click()
                page.wait_for_timeout(3000)
                # Check current active page number or result range
                res_pag_text = page.locator(".resultats.clearfix .result_pag").first.inner_text()
                print("Result text after next page:", res_pag_text)

        browser.close()

if __name__ == "__main__":
    test()
