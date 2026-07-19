"""INRIA Jobs scraper — server-rendered HTML with keyword search."""

import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class INRIAScraper(BaseScraper):
    SOURCE_NAME = "inria"

    BASE_URL = "https://jobs.inria.fr"
    SEARCH_URL = f"{BASE_URL}/public/classic/fr/offres"

    def scrape(self) -> list[dict]:
        keyword = self.config.get("inria", {}).get("keyword", "CIFRE")

        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            # GET the page first to obtain the CSRF token
            resp = session.get(self.SEARCH_URL, params={"locale": "fr"}, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Find the CSRF token
            token_input = soup.find("input", {"id": "recherche_offre__token"})
            token = token_input["value"] if token_input else ""

            # Submit search form via POST
            form_data = {
                "recherche_offre[motsClef]": keyword,
                "recherche_offre[fonctionOffre]": "",
                "recherche_offre[domaineActivite]": "",
                "recherche_offre[themeOffre]": "",
                "recherche_offre[typeContrat]": "",
                "recherche_offre[CRI]": "",
                "recherche_offre[rechercher]": "",
                "recherche_offre[_token]": token,
            }

            resp2 = session.post(self.SEARCH_URL, data=form_data, timeout=30)
            resp2.raise_for_status()
            return self._parse_results(resp2.text)

        except Exception as e:
            print(f"[inria] Scraping failed: {e}")
            return []

    def _parse_results(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        offers = []

        # INRIA lists offers as cards/links. Look for offer detail links
        offer_cards = soup.select("a[href*='/public/classic/fr/offres/detail/']")

        for card in offer_cards:
            href = card.get("href", "")
            if not href:
                continue

            title = self._clean(card.get_text())
            if not title or len(title) < 5:
                continue

            full_link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            # Try to extract extra info from surrounding elements
            parent = card.find_parent("div") or card.find_parent("li")
            description = ""
            company = "INRIA"
            if parent:
                desc_parts = parent.find_all(string=True)
                description = self._clean(" ".join(desc_parts))[:500]

            offers.append({
                "title": title,
                "company": company,
                "description": description,
                "link": full_link,
            })

        print(f"[inria] Found {len(offers)} offers")
        return offers
