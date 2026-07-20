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
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            })

            # GET the page first to obtain the CSRF token
            resp = session.get(self.SEARCH_URL, params={"locale": "fr"}, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Find the CSRF token
            token_input = soup.find("input", {"id": "recherche_offre__token"})
            token = token_input["value"] if token_input and token_input.has_attr("value") else ""

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

            resp2 = session.post(self.SEARCH_URL, params={"locale": "fr"}, data=form_data, timeout=30)
            resp2.raise_for_status()
            return self._parse_results(resp2.text)

        except Exception as e:
            print(f"[inria] Scraping failed: {e}")
            return []

    def _parse_results(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        offers = []

        offer_lis = soup.select("li.resultats")

        for li in offer_lis:
            link_el = li.select_one("a.list-offres-link") or li.select_one("h2 a")
            if not link_el:
                continue

            href = link_el.get("href", "")
            if not href:
                continue

            full_link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            title = self._clean(" ".join(link_el.stripped_strings))
            if not title or len(title) < 5:
                continue

            infos = []
            for info_li in li.select("ul.infos-liste-offre-inria li"):
                info_text = self._clean(" ".join(info_li.stripped_strings))
                if info_text:
                    infos.append(info_text)

            description = " | ".join(infos) if infos else title

            offers.append({
                "title": title,
                "company": "INRIA",
                "description": description,
                "link": full_link,
            })

        print(f"[inria] Found {len(offers)} offers")
        return offers
