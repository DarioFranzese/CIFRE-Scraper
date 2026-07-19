"""CEA Jobs scraper — server-rendered HTML with form-based search."""

import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class CEAScraper(BaseScraper):
    SOURCE_NAME = "cea"

    BASE_URL = "https://www.emploi.cea.fr"
    SEARCH_URL = f"{BASE_URL}/offre-de-emploi/liste-offres.aspx"

    def scrape(self) -> list[dict]:
        cea_config = self.config.get("cea", {})
        keyword = cea_config.get("keyword", "these")

        try:
            # First, GET the search page to obtain __VIEWSTATE and other hidden fields
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            resp = session.get(self.SEARCH_URL, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Extract ASP.NET hidden fields
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})
            viewstate_val = viewstate["value"] if viewstate else ""
            generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            generator_val = generator["value"] if generator else ""
            validation = soup.find("input", {"name": "__EVENTVALIDATION"})
            validation_val = validation["value"] if validation else ""

            # Find the keyword input field name
            keyword_input = soup.find("input", id=lambda x: x and "Keywords" in str(x))
            keyword_name = keyword_input["name"] if keyword_input else "ctl00$ctl00$moteurRapideOffre$ctl00$OfferCriteria_Keywords"

            # Find the search button's name & value
            search_button = soup.find("input", id=lambda x: x and "BT_recherche" in str(x))
            button_name = search_button["name"] if search_button else "ctl00$ctl00$moteurRapideOffre$BT_recherche"
            button_value = search_button.get("value", "Lancer ma recherche") if search_button else "Lancer ma recherche"

            # Submit the search form
            form_data = {
                "__VIEWSTATE": viewstate_val,
                "__VIEWSTATEGENERATOR": generator_val,
                "__EVENTVALIDATION": validation_val,
                keyword_name: keyword,
                button_name: button_value,
            }

            resp2 = session.post(self.SEARCH_URL, data=form_data, timeout=30)
            resp2.raise_for_status()

            # Retrieve pages recursively or in a loop
            current_html = resp2.text
            offers = []
            seen_links = set()

            while True:
                # Parse current page offers
                page_soup = BeautifulSoup(current_html, "lxml")
                for a in page_soup.find_all("a"):
                    href = a.get("href", "")
                    if not href or href in seen_links:
                        continue

                    # Only actual job detail links (they contain "/offre-de-emploi/emploi-")
                    if "/offre-de-emploi/emploi-" not in href:
                        continue

                    seen_links.add(href)
                    title = self._clean(a.get_text())
                    if not title or len(title) < 5:
                        continue

                    # Check that "These", "THESE", "these" or "Thèse" are in the title
                    title_lower = title.lower()
                    if "these" not in title_lower and "thèse" not in title_lower:
                        continue

                    full_link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

                    offers.append({
                        "title": title,
                        "company": "CEA",
                        "description": "",
                        "link": full_link,
                    })

                # Check if there is a next page link
                next_link = page_soup.find("a", id=lambda x: x and "linkSuivPage" in str(x))
                if next_link and next_link.get("href"):
                    next_url = next_link.get("href")
                    if not next_url.startswith("http"):
                        next_url = f"{self.BASE_URL}{next_url}"

                    resp_next = session.get(next_url, timeout=30)
                    resp_next.raise_for_status()
                    current_html = resp_next.text
                else:
                    break

            # Fetch descriptions for the matching offers
            for offer in offers:
                try:
                    detail_resp = session.get(
                        offer["link"],
                        timeout=15,
                    )
                    if detail_resp.ok:
                        detail_soup = BeautifulSoup(detail_resp.text, "lxml")
                        desc_el = detail_soup.find("div", class_=lambda c: c and "description" in str(c).lower())
                        if desc_el:
                            offer["description"] = self._clean(desc_el.get_text())[:1500]
                except Exception:
                    pass

            print(f"[cea] Found {len(offers)} offers")
            return offers

        except Exception as e:
            print(f"[cea] Scraping failed: {e}")
            return []
