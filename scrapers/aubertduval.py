"""Aubert & Duval Jobs scraper — server-rendered HTML with form search."""

import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class AubertDuvalScraper(BaseScraper):
    SOURCE_NAME = "aubertduval"

    URL = "https://www.aubertduval.com/carriere/offres-demplois/"

    def scrape(self) -> list[dict]:
        ad_config = self.config.get("aubertduval", {})
        contrat_val = ad_config.get("contrat", "these-cifre-166763")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        }

        offers = []
        page = 1

        while True:
            data = {
                "page_": str(page),
                "contrat": contrat_val,
                "search": "true",
                "lang": "fr_FR",
            }

            try:
                resp = requests.post(self.URL, data=data, headers=headers, timeout=30)
                resp.raise_for_status()
                resp.encoding = "utf-8"
            except Exception as e:
                print(f"[aubertduval] Request failed on page {page}: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            blocs = soup.find("div", class_="blocs")

            if not blocs:
                break

            page_offers = blocs.find_all("a", href=True)
            if not page_offers:
                break

            found_on_page = 0
            for a in page_offers:
                h3 = a.find("h3")
                title = self._clean(h3.get_text(strip=True)) if h3 else ""
                link = a["href"]

                if not title or not link:
                    continue

                infos = a.find("div", class_="infos")
                desc_parts = []
                if infos:
                    for p_tag in infos.find_all("p"):
                        txt = self._clean(p_tag.get_text(strip=True))
                        if txt:
                            desc_parts.append(txt)

                description = " | ".join(desc_parts)

                offers.append({
                    "title": title,
                    "company": "Aubert & Duval",
                    "description": description,
                    "link": link,
                })
                found_on_page += 1

            if found_on_page == 0:
                break

            # Check if there is pagination indicating another page
            pagination = soup.find("div", class_="pagination")
            if not pagination or not pagination.find_all("a"):
                # No next page links found
                break

            page += 1

        print(f"[aubertduval] Found {len(offers)} offers")
        return offers
