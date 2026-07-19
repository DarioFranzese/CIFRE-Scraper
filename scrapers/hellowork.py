"""HelloWork scraper — server-rendered HTML job board."""

import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class HelloWorkScraper(BaseScraper):
    SOURCE_NAME = "hellowork"

    SEARCH_URL = "https://www.hellowork.com/fr-fr/emploi/recherche.html"

    def scrape(self) -> list[dict]:
        skip_companies = [c.lower() for c in self.config.get("skip_companies_on_aggregators", [])]

        try:
            resp = requests.get(
                self.SEARCH_URL,
                params={
                    "k": "CIFRE",
                    "k_autocomplete": "",
                    "l": "",
                    "l_autocomplete": "",
                    "st": "relevance",
                    "msa": "0",
                    "d": "w",  # posted within last week
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                },
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[hellowork] Request failed: {e}")
            return []

        return self._parse_results(resp.text, skip_companies)

    def _parse_results(self, html: str, skip_companies: list[str]) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        offers = []

        # HelloWork renders job cards as <a> or <article> elements
        # Look for job listing links
        job_cards = soup.select("a[href*='/fr-fr/emploi/']")

        seen_links = set()
        for card in job_cards:
            href = card.get("href", "")
            if not href or href in seen_links or "/recherche.html" in href:
                continue
            # Only detail pages
            if not href.endswith(".html") or "/emploi/" not in href:
                continue

            seen_links.add(href)

            # Extract title and company from card content
            title_el = card.find(["h2", "h3", "span"], class_=lambda c: c and "title" in str(c).lower()) or card
            title = self._clean(title_el.get_text())

            if not title or len(title) < 5:
                continue

            # Try to find company name
            company = ""
            parent = card.find_parent(["article", "div", "li"])
            if parent:
                company_el = parent.find(string=True, recursive=True)
                # Look for company-related elements
                for el in parent.find_all(["span", "p", "div"]):
                    classes = " ".join(el.get("class", []))
                    if "company" in classes.lower() or "entreprise" in classes.lower():
                        company = self._clean(el.get_text())
                        break

            # Skip companies already covered by dedicated scrapers
            if company and company.lower() in skip_companies:
                continue

            full_link = href if href.startswith("http") else f"https://www.hellowork.com{href}"

            # Description from card
            description = ""
            if parent:
                desc_el = parent.find(["p", "div"], class_=lambda c: c and ("desc" in str(c).lower() or "teaser" in str(c).lower()))
                if desc_el:
                    description = self._clean(desc_el.get_text())[:500]

            offers.append({
                "title": title,
                "company": company or "Unknown",
                "description": description,
                "link": full_link,
            })

        print(f"[hellowork] Found {len(offers)} offers")
        return offers
