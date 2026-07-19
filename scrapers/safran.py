"""Safran Jobs scraper — JS-rendered, requires Playwright."""

from scrapers.base import BaseScraper


class SafranScraper(BaseScraper):
    SOURCE_NAME = "safran"

    SEARCH_URL = "https://www.safran-group.com/jobs?search=cifre"

    def scrape(self) -> list[dict]:
        cfg = self.config.get("safran", {})
        allowed_tags = [t.lower() for t in cfg.get("allowed_tags", [
            "IT", "Mathematics and algorithms", "Data",
            "Architecture and systems engineering"
        ])]

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[safran] Playwright not installed — skipping")
            return []

        offers = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                )
                page = context.new_page()
                page.add_init_script("delete navigator.__proto__.webdriver;")

                page.goto(self.SEARCH_URL, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(5000)

                # Look for job cards using the exact selector provided by the user
                cards = page.locator("div.c-offer-item").all()
                print(f"[safran] Found {len(cards)} raw cards on page")

                for card in cards:
                    try:
                        text = card.inner_text(timeout=3000)
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        if not lines:
                            continue

                        title = lines[0]

                        # Check the last tag/badge — must be in allowed_tags
                        tags = [line for line in lines if len(line) < 60]
                        tag_ok = False
                        if tags:
                            last_tag = tags[-1].lower()
                            if any(allowed in last_tag for allowed in allowed_tags):
                                tag_ok = True
                        else:
                            tag_ok = True  # If we can't find tags, include by default

                        if not tag_ok:
                            continue

                        # Get link
                        link_el = card.locator("a").first
                        href = ""
                        try:
                            href = link_el.get_attribute("href", timeout=1000)
                        except Exception:
                            pass
                        if href and not href.startswith("http"):
                            href = f"https://www.safran-group.com{href}"

                        # Fetch detail page description using a fresh browser session to bypass Cloudflare
                        description = ""
                        if href:
                            description = self._fetch_description(browser, href)

                        offers.append({
                            "title": self._clean(title),
                            "company": "Safran",
                            "description": self._clean(description)[:1500] if description else "No description available",
                            "link": href or self.SEARCH_URL,
                        })
                    except Exception as e:
                        print(f"[safran] Error parsing card: {e}")
                        continue

                browser.close()

        except Exception as e:
            print(f"[safran] Scraping failed: {e}")

        print(f"[safran] Found {len(offers)} offers")
        return offers

    def _fetch_description(self, browser, url: str) -> str:
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            )
            page = context.new_page()
            page.add_init_script("delete navigator.__proto__.webdriver;")

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            body_text = page.locator("body").inner_text()

            desc_start = body_text.find("Job Description")
            if desc_start == -1:
                desc_start = body_text.find("Description du poste")
            if desc_start == -1:
                desc_start = body_text.find("Description de la mission")

            description = ""
            if desc_start != -1:
                description = body_text[desc_start:].strip()
                company_idx = description.find("Company Information")
                if company_idx != -1:
                    description = description[:company_idx].strip()
                else:
                    locate_idx = description.find("Locate your future workplace")
                    if locate_idx != -1:
                        description = description[:locate_idx].strip()

            context.close()
            return description
        except Exception as e:
            print(f"[safran] Error fetching detail page {url}: {e}")
            return ""
