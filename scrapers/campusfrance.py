"""Campus France (La Recherche en France - Doctorat) scraper.

Navigates to https://recherche-recette.campusfrance.org/phd/offers,
expands funding filters, selects CIFRE funding, triggers search,
adjusts table page length to load all offers, and parses detailed offer descriptions.
"""

import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper


class CampusFranceScraper(BaseScraper):
    SOURCE_NAME = "campusfrance"

    BASE_URL = "https://recherche-recette.campusfrance.org"
    SEARCH_URL = "https://recherche-recette.campusfrance.org/phd/offers"

    def scrape(self) -> list[dict]:
        """Scrape CIFRE PhD offers from Campus France."""
        cfg = self.config.get("campusfrance", {})
        search_url = cfg.get("search_url", self.SEARCH_URL)

        offers = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            try:
                print(f"[{self.SOURCE_NAME}] Navigating to {search_url}")
                page.goto(search_url, timeout=60000)
                page.wait_for_load_state("networkidle")

                # 1. Expand sidebar filter for 'Financement' if collapsed
                # Check if filter container is hidden
                fc_selector = '#f_funding'
                try:
                    # Open Financement filter accordion
                    financement_header = page.locator('.col-sm-3.sidebar-filters').locator('text=Financement').first
                    if financement_header.count() > 0:
                        financement_header.click()
                        page.wait_for_timeout(800)
                except Exception as e:
                    print(f"[{self.SOURCE_NAME}] Note on opening accordion: {e}")

                # Ensure filter-container is displayed
                page.evaluate('''() => {
                    const el = document.querySelector("#f_funding");
                    if (el) {
                        const container = el.closest(".filter-container");
                        if (container) {
                            container.style.display = "block";
                        }
                    }
                }''')

                # 2. Select option value='cifre'
                print(f"[{self.SOURCE_NAME}] Selecting 'cifre' funding filter")
                page.select_option("#f_funding", "cifre")

                # 3. Click button id='btn_search'
                print(f"[{self.SOURCE_NAME}] Submitting search...")
                with page.expect_response(
                    lambda resp: "phd/offers" in resp.url and resp.status == 200,
                    timeout=30000
                ):
                    page.click("#btn_search")

                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)

                # 4. Expand page length to 250 to ensure all offers are displayed in a single page
                try:
                    length_select = page.locator('select[name="maintable_length"]')
                    if length_select.count() > 0:
                        print(f"[{self.SOURCE_NAME}] Setting display length to 250")
                        try:
                            with page.expect_response(
                                lambda resp: "ajax_dtlist" in resp.url and resp.status == 200,
                                timeout=10000
                            ):
                                length_select.select_option("250")
                        except Exception:
                            # If no extra records or no AJAX triggered, trigger via DataTable API
                            page.evaluate('''() => {
                                if (window.jQuery && window.jQuery.fn.dataTable) {
                                    window.jQuery('#maintable').DataTable().page.len(250).draw();
                                }
                            }''')
                        page.wait_for_load_state("networkidle")
                        page.wait_for_timeout(1500)
                except Exception as e:
                    print(f"[{self.SOURCE_NAME}] Note on setting length to 250: {e}")

                # 5. Extract offer rows from #maintable
                table_rows = page.locator("#maintable tbody tr").all()
                print(f"[{self.SOURCE_NAME}] Found {len(table_rows)} table row(s)")

                offer_stubs = []
                for row in table_rows:
                    row_id = row.get_attribute("id")
                    if not row_id or "no-data" in row_id:
                        continue

                    # Extract title and company / institution from row HTML
                    row_html = row.inner_html()
                    soup_row = BeautifulSoup(row_html, "html.parser")
                    
                    # Row title is located inside div.h3
                    title_div = soup_row.find(class_=lambda c: c and "h3" in c if isinstance(c, list) else (c and "h3" in c))
                    row_title = title_div.get_text(strip=True) if title_div else ""

                    # Find possible company name (first non-empty div after title div inside .click)
                    company = ""
                    click_div = soup_row.find("div", class_=lambda c: c and "click" in c if isinstance(c, list) else (c and "click" in c))
                    if click_div:
                        candidate_divs = click_div.find_all("div", class_="marginb5", recursive=False)
                        for c_div in candidate_divs:
                            # Skip if it contains icons or spans for tags/disciplines
                            if c_div.find(["i", "span", "br"]):
                                continue
                            c_text = c_div.get_text(strip=True).strip(" |")
                            if c_text and not any(tag in c_text.lower() for tag in ["date", "sciences", "doctorat", "contexte", "we are offering"]):
                                company = c_text
                                break

                    offer_stubs.append({
                        "id": row_id,
                        "title": row_title,
                        "link": f"{self.BASE_URL}/{row_id}",
                        "company": company or "Campus France",
                    })

                # 6. Fetch details for each offer stub
                for stub in offer_stubs:
                    detail = self._fetch_offer_detail(page, stub)
                    if detail:
                        offers.append(detail)

            except Exception as e:
                print(f"[{self.SOURCE_NAME}] Error during scrape: {e}")
            finally:
                browser.close()

        print(f"[{self.SOURCE_NAME}] Successfully scraped {len(offers)} CIFRE offer(s)")
        return offers

    def _fetch_offer_detail(self, page, stub: dict) -> dict | None:
        """Navigate to offer detail page and extract title, description, and metadata."""
        link = stub["link"]
        try:
            print(f"[{self.SOURCE_NAME}] Fetching detail for {link}")
            page.goto(link, timeout=45000)
            page.wait_for_load_state("networkidle")

            soup = BeautifulSoup(page.content(), "html.parser")

            # Extract title: page title format "La Recherche en France - {ID} {Title}"
            page_title = soup.title.get_text(strip=True) if soup.title else ""
            title = re.sub(r"^La Recherche en France\s*-\s*[A-Z0-9]+\s*", "", page_title).strip()
            if not title or len(title) < 5:
                title = stub.get("title", "")
            if not title:
                # Fallback to heading
                h_elem = soup.find(["h2", "h3"])
                title = h_elem.get_text(strip=True) if h_elem else stub["id"]

            # Extract description
            desc_h4 = soup.find(lambda t: t.name == "h4" and "Description" in t.text)
            description = ""
            if desc_h4:
                desc_container = desc_h4.parent
                # Clean out the 'Description' label itself
                full_text = desc_container.get_text("\n", strip=True)
                description = re.sub(r"^Description\s*", "", full_text).strip()

            # Extract institution / employer if not yet established
            company = stub.get("company", "")
            if not company or company == "Campus France / Unknown":
                # Look for Institution d'accueil or Laboratoire
                for dl in soup.find_all("dl"):
                    dt_text = dl.get_text(" ", strip=True)
                    if "Institution d'accueil" in dt_text or "Laboratoire" in dt_text:
                        dd = dl.find("dd")
                        if dd and dd.get_text(strip=True):
                            company = dd.get_text(strip=True)
                            break

            return {
                "title": self._clean(title),
                "company": self._clean(company or "Campus France"),
                "description": self._clean(description),
                "link": link,
            }
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Failed to fetch detail for {link}: {e}")
            return None
