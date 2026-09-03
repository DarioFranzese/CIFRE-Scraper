"""France Travail scraper — searches for CIFRE PhD offers, handles dynamic pagination, and extracts detail pages."""

import re
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class FranceTravailScraper(BaseScraper):
    SOURCE_NAME = "francetravail"

    DEFAULT_SEARCH_URL = (
        "https://candidat.francetravail.fr/offres/recherche"
        "?motsCles=cifre&offresPartenaires=true&range=0-19&rayon=10&tri=1"
    )
    DETAIL_BASE_URL = "https://candidat.francetravail.fr/offres/recherche/detail/{}"

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
        """Scrape CIFRE offers from France Travail."""
        cfg = self.config.get("francetravail", {})
        search_url = cfg.get("search_url", self.DEFAULT_SEARCH_URL)
        max_clicks = cfg.get("max_pagination_clicks", 10)

        offer_ids, card_metadata = self._fetch_listing_with_playwright(
            search_url=search_url,
            max_clicks=max_clicks,
        )

        print(f"[francetravail] Extracted {len(offer_ids)} offer IDs from search page")

        offers = []
        skip_companies = [c.lower() for c in self.config.get("skip_companies_on_aggregators", [])]

        for offer_id in offer_ids:
            try:
                card_info = card_metadata.get(offer_id, {})
                offer = self._fetch_offer_detail(offer_id, card_info)
                if not offer:
                    continue

                # Filter out companies already scraped directly if found in skip list
                comp = (offer.get("company") or "").lower()
                if comp and any(skip in comp for skip in skip_companies):
                    print(f"[francetravail] Skipping '{offer['title']}' from skipped company '{offer['company']}'")
                    continue

                offers.append(offer)
            except Exception as e:
                print(f"[francetravail] Error processing offer {offer_id}: {e}")

        print(f"[francetravail] Successfully scraped {len(offers)} offers")
        return offers

    def _fetch_listing_with_playwright(
        self,
        search_url: str,
        max_clicks: int = 10,
    ) -> tuple[list[str], dict[str, dict]]:
        """Navigate to search listing and click 'load more' button until done.

        Returns:
            (list_of_offer_ids, dict_of_metadata_by_id)
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[francetravail] Playwright not installed — falling back to static requests")
            return self._fetch_listing_fallback(search_url)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                )
                page = context.new_page()
                page.add_init_script("delete navigator.__proto__.webdriver;")

                print(f"[francetravail] Navigating to: {search_url}")
                page.goto(search_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(2000)

                # Remove cookie modal banner so it doesn't intercept click events
                self._dismiss_cookie_banner(page)

                # Paginate by clicking the 'load more' button
                clicks = 0
                more_selector = (
                    ".results-more a, .result-more a, "
                    ".results-more button, .result-more button, "
                    "p[class*='result-more'] a, p[class*='results-more'] a"
                )

                while clicks < max_clicks:
                    # Remove cookies again in case dynamically re-injected
                    self._dismiss_cookie_banner(page)

                    more_btn = page.locator(more_selector)
                    if more_btn.count() == 0:
                        break

                    btn = more_btn.first
                    if not btn.is_visible():
                        break

                    prev_count = page.locator("li[data-id-offre], li[data-id-offer]").count()
                    print(f"[francetravail] Clicking 'load more' button (click #{clicks + 1}, currently {prev_count} items)...")

                    try:
                        btn.click(timeout=5000)
                    except Exception:
                        # Fallback click via JS evaluate
                        btn.evaluate("el => el.click()")

                    page.wait_for_timeout(2500)
                    new_count = page.locator("li[data-id-offre], li[data-id-offer]").count()

                    if new_count <= prev_count:
                        # No new items loaded, stop pagination
                        break

                    clicks += 1

                # Parse the final page HTML with BeautifulSoup
                html_content = page.content()
                browser.close()

                return self._parse_cards_from_html(html_content)

        except Exception as e:
            print(f"[francetravail] Playwright listing navigation failed: {e}. Falling back to requests.")
            return self._fetch_listing_fallback(search_url)

    @staticmethod
    def _dismiss_cookie_banner(page) -> None:
        """Remove cookie banner overlay and backdrops if present."""
        page.evaluate("""() => {
            const cookies = document.querySelector('pe-cookies');
            if (cookies) cookies.remove();
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }""")

    def _fetch_listing_fallback(self, search_url: str) -> tuple[list[str], dict[str, dict]]:
        """Fallback to requests when Playwright is unavailable or fails."""
        try:
            resp = self.session.get(search_url, timeout=30)
            resp.raise_for_status()
            return self._parse_cards_from_html(resp.text)
        except Exception as e:
            print(f"[francetravail] Fallback listing request failed: {e}")
            return [], {}

    def _parse_cards_from_html(self, html: str) -> tuple[list[str], dict[str, dict]]:
        """Extract offer IDs and card metadata from raw HTML."""
        soup = BeautifulSoup(html, "lxml")
        offer_ids = []
        card_metadata = {}

        # Look for <li data-id-offer="..." class="result"> or data-id-offre
        cards = soup.select("li.result[data-id-offre], li.result[data-id-offer]")
        if not cards:
            cards = soup.select("li[data-id-offre], li[data-id-offer]")

        for card in cards:
            oid = card.get("data-id-offre") or card.get("data-id-offer")
            if not oid:
                link_el = card.select_one("a[href*='/offres/recherche/detail/']")
                if link_el and link_el.get("href"):
                    m = re.search(r"/detail/([^/?#]+)", link_el["href"])
                    if m:
                        oid = m.group(1)

            if not oid or oid in card_metadata:
                continue

            # Card title fallback
            title_el = card.select_one(".media-heading-title, h2, h3")
            card_title = self._clean(title_el.get_text()) if title_el else ""

            # Card subtext (often contains company or location, e.g. "Safran - 27 - Vernon")
            subtext_el = card.select_one("p.subtext, .subtext")
            card_subtext = self._clean(subtext_el.get_text()) if subtext_el else ""

            card_company = ""
            if card_subtext:
                parts = [p.strip() for p in card_subtext.split(" - ") if p.strip()]
                # If first part is not numeric (department code like '71'), it's likely the company
                if parts and not re.match(r"^\d{2,3}$", parts[0]):
                    card_company = parts[0]

            offer_ids.append(oid)
            card_metadata[oid] = {
                "card_title": card_title,
                "card_company": card_company,
                "card_subtext": card_subtext,
            }

        return offer_ids, card_metadata

    def _fetch_offer_detail(self, offer_id: str, card_info: dict) -> dict | None:
        """Fetch and parse the detailed offer page."""
        detail_url = self.DETAIL_BASE_URL.format(offer_id)

        try:
            resp = self.session.get(detail_url, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            print(f"[francetravail] Failed to fetch detail {detail_url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # 1. Extract title from itemprop="title"
        title = ""
        title_el = soup.find(attrs={"itemprop": "title"})
        if title_el:
            title = self._clean(title_el.get_text())

        if not title:
            h1 = soup.select_one("h1.title, h1")
            if h1:
                # Often preceded by "Offre n°XXXXXXX"
                raw_h1 = self._clean(h1.get_text())
                title = re.sub(r"^Offre\s+n[°\d\s]+", "", raw_h1).strip()

        if not title:
            title = card_info.get("card_title", "")

        if not title:
            return None

        # 2. Extract description from itemprop="description"
        description = ""
        desc_el = soup.find(attrs={"itemprop": "description"})
        if desc_el:
            description = self._clean(desc_el.get_text())
        if not description:
            desc_el = soup.select_one("p.description, div.description")
            if desc_el:
                description = self._clean(desc_el.get_text())

        # 3. Extract company
        company = ""
        h3_title = soup.find("h3", class_="title")
        if h3_title:
            company = self._clean(h3_title.get_text())

        if not company:
            hiring_org = soup.find(attrs={"itemprop": "hiringOrganization"})
            if hiring_org:
                company = self._clean(hiring_org.get_text())

        if not company:
            company = card_info.get("card_company", "")

        if not company:
            company = "France Travail"

        return {
            "title": title,
            "company": company,
            "description": description,
            "link": detail_url,
        }


if __name__ == "__main__":
    scraper = FranceTravailScraper()
    results = scraper.run()
    print(f"\nFinal result: {len(results)} offers extracted")
    for r in results[:5]:
        print(f"[{r['id']}] {r['title']} | {r['company']} | {r['link']}")
