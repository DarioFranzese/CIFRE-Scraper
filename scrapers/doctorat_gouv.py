"""Doctorat.gouv.fr scraper — Angular SPA, requires Playwright."""

from scrapers.base import BaseScraper


class DoctoratGouvScraper(BaseScraper):
    SOURCE_NAME = "doctorat_gouv"

    BASE_URL = "https://app.doctorat.gouv.fr"

    def scrape(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[doctorat_gouv] Playwright not installed — skipping")
            return []

        offers = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                page.goto(self.BASE_URL, wait_until="networkidle", timeout=60000)

                # Wait for Angular to render the search input
                search_input = page.locator('input#query[type="search"]')
                search_input.wait_for(state="visible", timeout=15000)

                # Type the keyword — the SPA auto-updates results, no Enter needed
                search_input.fill("CIFRE")

                # Wait for the result cards to appear
                card_selector = "div.fr-card.fr-card--shadow.fr-card--sm.card-clickable"
                page.locator(card_selector).first.wait_for(state="visible", timeout=15000)
                # Extra pause for Angular to finish rendering all cards
                page.wait_for_timeout(3000)

                cards = page.locator(card_selector).all()
                print(f"[doctorat_gouv] Found {len(cards)} cards on search page")
                
                detail_urls = []
                for card in cards:
                    try:
                        link_el = card.locator("a").first
                        href = link_el.get_attribute("href")
                        if href:
                            if not href.startswith("http"):
                                href = f"{self.BASE_URL}{href}"
                            detail_urls.append(href)
                    except Exception:
                        continue

                # Visit detail pages to parse metadata, description, and title
                for url in detail_urls:
                    try:
                        detail_page = context.new_page()
                        detail_page.goto(url, wait_until="domcontentloaded")
                        detail_page.wait_for_timeout(2000)

                        body_text = detail_page.locator("body").inner_text()

                        # Extract Établissement
                        establishment = ""
                        for line in body_text.split("\n"):
                            if "établissement" in line.lower():
                                parts = line.split(":", 1)
                                if len(parts) > 1:
                                    establishment = parts[1].strip()
                                    break

                        # Extract Laboratoire
                        lab = ""
                        for line in body_text.split("\n"):
                            if "laboratoire de recherche" in line.lower():
                                parts = line.split(":", 1)
                                if len(parts) > 1:
                                    lab = parts[1].strip()
                                    break

                        # Extract Title
                        title = detail_page.locator("h1").first.inner_text().strip()

                        # Extract Description
                        desc_start = body_text.find("Résumé")
                        if desc_start == -1:
                            desc_start = body_text.find("Objectif et Contexte")

                        description = ""
                        if desc_start != -1:
                            description = body_text[desc_start:].strip()
                            footer_idx = description.find("Prendre contact")
                            if footer_idx != -1:
                                description = description[:footer_idx].strip()

                        offers.append({
                            "title": self._clean(title),
                            "company": self._clean(lab or establishment or "Unknown"),
                            "description": self._clean(description)[:1500],
                            "link": url
                        })

                        detail_page.close()
                    except Exception as e:
                        print(f"[doctorat_gouv] Error parsing detail page {url}: {e}")

                browser.close()

        except Exception as e:
            print(f"[doctorat_gouv] Scraping failed: {e}")

        print(f"[doctorat_gouv] Found {len(offers)} offers")
        return offers
