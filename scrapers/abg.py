"""Association Bernard Gregory (ABG) scraper.

Searches for CIFRE PhD offers on https://www.abg.asso.fr/fr/candidatOffres,
handles dynamic Prototype.js AJAX pagination, and extracts detailed offer information.
"""

import time
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class ABGScraper(BaseScraper):
    SOURCE_NAME = "abg"

    BASE_URL = "https://www.abg.asso.fr"
    SEARCH_URL = "https://www.abg.asso.fr/fr/candidatOffres"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def scrape(self) -> list[dict]:
        """Scrape CIFRE PhD offers from Association Bernard Gregory."""
        abg_cfg = self.config.get("abg", {})
        keyword = abg_cfg.get("keyword", "CIFRE")
        max_pages = abg_cfg.get("max_pages", 10)

        # 1. Fetch offer card references via Playwright (handling search and AJAX pagination)
        cards = self._fetch_cards_with_playwright(keyword=keyword, max_pages=max_pages)
        print(f"[abg] Extracted {len(cards)} offer cards from search listing")

        # 2. Extract detailed info for each offer and apply filters
        skip_companies = [c.lower() for c in self.config.get("skip_companies_on_aggregators", [])]
        offers = []

        for card in cards:
            link = card.get("link", "")
            if not link:
                continue

            try:
                detail = self._fetch_offer_detail(link, card)
                if not detail:
                    continue

                comp = (detail.get("company") or "").lower()
                if comp and any(skip in comp for skip in skip_companies):
                    print(f"[abg] Skipping '{detail['title']}' from excluded company '{detail['company']}'")
                    continue

                offers.append(detail)
            except Exception as e:
                print(f"[abg] Error fetching detail for {link}: {e}")

        print(f"[abg] Successfully scraped {len(offers)} offers")
        return offers

    def _fetch_cards_with_playwright(self, keyword: str = "CIFRE", max_pages: int = 10) -> list[dict]:
        """Navigate to ABG search, enter keyword, and paginate through AJAX results."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[abg] Playwright not installed — cannot run dynamic AJAX pagination")
            return []

        cards = []
        seen_links = set()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                )
                page = context.new_page()

                print(f"[abg] Navigating to: {self.SEARCH_URL}")
                page.goto(self.SEARCH_URL, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(1500)

                # Keyword input: input[name="criteria[mot_cle]"]
                kw_input = page.locator('input[name="criteria[mot_cle]"], #criteria_mot_cle')
                if kw_input.count() > 0 and keyword:
                    kw_input.first.fill(keyword)
                    print(f"[abg] Filled keyword: '{keyword}'")
                    # Submit search via #monBoutonSubmit (which executes the Ajax.Updater with criteria)
                    submit_btn = page.locator("#monBoutonSubmit")
                    if submit_btn.count() > 0:
                        submit_btn.first.evaluate("el => el.click()")
                    else:
                        kw_input.first.press("Enter")
                elif not keyword:
                    # If keyword is empty, trigger reset button (#monBoutonReset) or submit directly
                    print("[abg] Empty keyword: triggering search/reset...")
                    reset_btn = page.locator("#monBoutonReset")
                    if reset_btn.count() > 0:
                        reset_btn.first.click()
                    else:
                        page.locator("#monBoutonSubmit").first.evaluate("el => el.click()")

                # Wait for the listing area to update
                page.wait_for_timeout(3000)

                current_page = 1
                while current_page <= max_pages:
                    # Extract offer cards on the current page
                    page_html = page.content()
                    page_cards = self._parse_cards_html(page_html)

                    new_on_page = 0
                    for c in page_cards:
                        if c["link"] not in seen_links:
                            seen_links.add(c["link"])
                            cards.append(c)
                            new_on_page += 1

                    print(f"[abg] Page {current_page}: found {len(page_cards)} cards ({new_on_page} new)")

                    # Check if pagination exists in class="resultats clearfix"
                    res_div = page.locator(".resultats.clearfix")
                    if res_div.count() == 0:
                        # No pagination block -> only 1 page of results
                        break

                    next_link = page.locator(".resultats.clearfix .pager_suiv a")
                    if next_link.count() == 0 or not next_link.first.is_visible():
                        # No further page available
                        break

                    # Get current pagination text before click to detect change
                    prev_pag_text = ""
                    pag_label = page.locator(".resultats.clearfix .result_pag")
                    if pag_label.count() > 0:
                        prev_pag_text = pag_label.first.inner_text()

                    print(f"[abg] Triggering AJAX next page event ({prev_pag_text.strip()})...")
                    try:
                        next_link.first.click(timeout=5000)
                    except Exception:
                        next_link.first.evaluate("el => el.click()")

                    # Wait for AJAX update
                    page.wait_for_timeout(2500)

                    # Check if page actually changed
                    new_pag_text = ""
                    if pag_label.count() > 0:
                        new_pag_text = pag_label.first.inner_text()

                    if new_pag_text and new_pag_text == prev_pag_text:
                        print("[abg] Pagination text did not change, reached last page")
                        break

                    current_page += 1

                browser.close()

        except Exception as e:
            print(f"[abg] Playwright session error: {e}")

        return cards

    def _parse_cards_html(self, html: str) -> list[dict]:
        """Extract card links and basic info from search result HTML."""
        soup = BeautifulSoup(html, "lxml")
        cards = []

        # Each offer item is <... class="item itLien it_offre ...">
        items = soup.select(".item.it_offre, .it_offre")
        for item in items:
            titre_logo = item.find(class_="titre_logo")
            if not titre_logo:
                continue

            a_tag = titre_logo.find("a")
            if not a_tag or not a_tag.get("href"):
                continue

            href = a_tag["href"]
            full_link = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            title = self._clean(a_tag.get_text())

            # Attempt to extract recruiter/company from card snippet
            company = ""
            card_strings = list(item.stripped_strings)
            # Typically layout is: [Title, Company, Type ('Thèse'), Location, Teaser...]
            if len(card_strings) >= 2 and card_strings[0] == title:
                company = self._clean(card_strings[1])

            cards.append({
                "title": title,
                "link": full_link,
                "card_company": company,
            })

        return cards

    def _fetch_offer_detail(self, link: str, card_info: dict) -> dict | None:
        """Fetch and parse the detailed offer page."""
        resp = self.session.get(link, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # 1. Extract title: prefer h1 in .offrePage
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = self._clean(h1.get_text())
        if not title:
            title = card_info.get("title", "")

        if not title:
            return None

        # 2. Extract company/recruiter: look for class="societe" or box_societe
        company = ""
        soc_el = soup.find(class_="societe")
        if soc_el:
            company = self._clean(soc_el.get_text())

        if not company:
            box_soc = soup.find(class_="box_societe")
            if box_soc:
                company = self._clean(box_soc.get_text())

        if not company:
            company = card_info.get("card_company", "")

        if not company:
            company = "Association Bernard Gregory"

        # 3. Extract description sections from .offrePage
        desc_parts = []
        inner_page = soup.find("div", class_="offrePage")
        if inner_page:
            for heading in inner_page.find_all(["h2", "h3"]):
                h_text = self._clean(heading.get_text())
                # Stop at login/registration prompts
                h_lower = h_text.lower()
                if "vous avez" in h_lower or "nouvel utilisateur" in h_lower or "postuler" in h_lower:
                    break

                sibling = heading.find_next_sibling()
                if sibling and any(c in sibling.get("class", []) for c in ["text", "societe"]):
                    body_text = self._clean(sibling.get_text())
                    if body_text:
                        desc_parts.append(f"{h_text}: {body_text}")

        description = "\n\n".join(desc_parts)

        return {
            "title": title,
            "company": company,
            "description": description,
            "link": link,
        }


if __name__ == "__main__":
    scraper = ABGScraper()
    results = scraper.run()
    print(f"\nFinal result: {len(results)} offers extracted")
    for r in results[:5]:
        print(f"[{r['id']}] {r['title']} | {r['company']} | {r['link']}")
