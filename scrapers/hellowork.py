"""HelloWork scraper — server-rendered HTML job board."""

import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class HelloWorkScraper(BaseScraper):
    SOURCE_NAME = "hellowork"

    SEARCH_URL = "https://www.hellowork.com/fr-fr/emploi/recherche.html"

    def scrape(self) -> list[dict]:
        try:
            resp = requests.get(
                self.SEARCH_URL,
                params={
                    "k": "CIFRE",
                    "k_autocomplete": "",
                    "l": "",
                    "l_autocomplete": "",
                    "st": "date",
                    "msa": "0",
                    "d": "all",
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                },
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[hellowork] Request failed: {e}")
            return []

        return self._parse_results(resp.text)

    def _parse_results(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        offers = []

        job_cards = soup.select('li[data-id-storage-target="item"]')

        for card in job_cards:
            # Extract job title
            title = ""
            title_input = card.select_one('input[name="title"]')
            if title_input and title_input.get("value"):
                title = self._clean(title_input.get("value"))
            if not title:
                title_el = card.select_one('[data-cy="offerTitle"] p.typo-l') or card.select_one('[data-cy="offerTitle"]')
                if title_el:
                    title = self._clean(title_el.get_text())

            if not title or len(title) < 5:
                continue

            # Extract company name
            company = ""
            company_input = card.select_one('input[name="company"]')
            if company_input and company_input.get("value"):
                company = self._clean(company_input.get("value"))
            if not company:
                company_el = card.select_one('[data-cy="offerTitle"] p.typo-s')
                if company_el:
                    company = self._clean(company_el.get_text())

            # Extract job detail link
            link = ""
            link_el = card.select_one('a[href*="/fr-fr/emplois/"]') or card.select_one('a[href*="/fr-fr/emploi/"]') or card.select_one('a[data-cy="offerTitle"]')
            if link_el and link_el.get("href"):
                href = link_el.get("href")
                link = href if href.startswith("http") else f"https://www.hellowork.com{href}"

            # Extract location & contract type for description
            loc_el = card.select_one('[data-cy="localisationCard"]')
            location = self._clean(loc_el.get_text()) if loc_el else ""

            contract_el = card.select_one('[data-cy="contractCard"]')
            contract = self._clean(contract_el.get_text()) if contract_el else ""

            desc_parts = [p for p in [location, contract] if p]
            description = " | ".join(desc_parts)

            offers.append({
                "title": title,
                "company": company or "Unknown",
                "description": description,
                "link": link,
            })

        print(f"[hellowork] Found {len(offers)} offers")
        return offers
