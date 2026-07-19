"""EDF Jobs scraper — Playwright-based due to 403 on plain requests."""

from scrapers.base import BaseScraper


class EDFScraper(BaseScraper):
    SOURCE_NAME = "edf"

    SEARCH_URL = "https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers?search[profil][34947]=34947"

    def scrape(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[edf] Playwright not installed — skipping")
            return []

        offers = []
        try:
            with sync_playwright() as p:
                # Use WebKit as it bypasses EDF's Akamai WAF block
                browser = p.webkit.launch(headless=True)
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()

                page.goto(self.SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                # Remove privacy overlays from DOM to prevent click/interception errors
                page.evaluate("""() => {
                    const selectors = ['#privacy-container', '#privacy-overlay', '[class*="cookie"]', '[class*="privacy"]'];
                    selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
                }""")

                cards = page.locator("li.offer").all()
                print(f"[edf] Found {len(cards)} raw cards on page")

                for card in cards:
                    try:
                        text = card.inner_text(timeout=3000).strip()
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        if not lines:
                            continue

                        # Line 0 is date (e.g. "11 July 2026"), Line 1 is title
                        title = lines[1] if len(lines) > 1 else lines[0]

                        # Get link
                        link_el = card.locator("a.offer-link").first
                        if not link_el.count():
                            link_el = card.locator("a").first

                        href = ""
                        if link_el.count():
                            href = link_el.get_attribute("href") or ""
                        if href and not href.startswith("http"):
                            href = f"https://www.edf.fr{href}"

                        # Fetch detail page description using a fresh browser context to bypass WAF
                        description = ""
                        if href:
                            description = self._fetch_description(browser, href)

                        offers.append({
                            "title": self._clean(title),
                            "company": "EDF",
                            "description": self._clean(description)[:1500] if description else "No description available",
                            "link": href or self.SEARCH_URL,
                        })
                    except Exception as e:
                        print(f"[edf] Error parsing card: {e}")
                        continue

                browser.close()

        except Exception as e:
            print(f"[edf] Scraping failed: {e}")

        print(f"[edf] Found {len(offers)} offers")
        return offers

    def _fetch_description(self, browser, url: str) -> str:
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            body_text = page.locator("body").inner_text()

            desc_start = body_text.find("Description of the offer")
            if desc_start == -1:
                desc_start = body_text.find("Description de l'offre")

            description = ""
            if desc_start != -1:
                description = body_text[desc_start:].strip()
                profile_idx = description.lower().find("profile")
                if profile_idx != -1:
                    description = description[:profile_idx].strip()
                else:
                    profile_idx = description.lower().find("profil")
                    if profile_idx != -1:
                        description = description[:profile_idx].strip()

            context.close()
            return description
        except Exception as e:
            print(f"[edf] Error fetching detail page {url}: {e}")
            return ""
