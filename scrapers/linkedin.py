"""LinkedIn Jobs scraper — public search, Playwright with stealth."""

from scrapers.base import BaseScraper


class LinkedInScraper(BaseScraper):
    SOURCE_NAME = "linkedin"

    SEARCH_URL = (
        "https://www.linkedin.com/jobs/search/"
        "?f_TPR=r604800"
        "&keywords=these%20cifre"
        "&location=France"
        "&origin=JOB_SEARCH_PAGE_JOB_FILTER"
    )

    def scrape(self) -> list[dict]:
        skip_companies = [c.lower() for c in self.config.get("skip_companies_on_aggregators", [])]

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[linkedin] Playwright not installed — skipping")
            return []

        offers = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="fr-FR",
                )
                page = context.new_page()

                # LinkedIn's public job search doesn't require login
                page.goto(self.SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                # LinkedIn may show an auth wall — check if we can see jobs
                job_cards = page.locator(".base-card, .job-search-card, .jobs-search__results-list > li").all()

                if not job_cards:
                    # Try alternative: scroll and wait
                    page.wait_for_timeout(5000)
                    job_cards = page.locator(".base-card, .result-card, li.jobs-search-results__list-item").all()

                for card in job_cards:
                    try:
                        # Title
                        title_el = card.locator("h3, .base-search-card__title, .result-card__title").first
                        title = self._clean(title_el.inner_text(timeout=2000))

                        # Company
                        company_el = card.locator("h4, .base-search-card__subtitle, .result-card__subtitle").first
                        company = self._clean(company_el.inner_text(timeout=2000))

                        # Skip companies already covered
                        if company.lower() in skip_companies:
                            continue

                        # Location
                        loc_el = card.locator(".job-search-card__location, .result-card__meta").first
                        location = ""
                        try:
                            location = self._clean(loc_el.inner_text(timeout=1000))
                        except Exception:
                            pass

                        # Link
                        link_el = card.locator("a").first
                        href = ""
                        try:
                            href = link_el.get_attribute("href", timeout=1000)
                        except Exception:
                            pass

                        if href and "?" in href:
                            href = href.split("?")[0]  # Clean tracking params

                        description = f"Location: {location}" if location else ""

                        offers.append({
                            "title": title,
                            "company": company or "Unknown",
                            "description": description,
                            "link": href or "",
                        })
                    except Exception:
                        continue

                browser.close()

        except Exception as e:
            print(f"[linkedin] Scraping failed (this is expected if blocked): {e}")

        print(f"[linkedin] Found {len(offers)} offers")
        return offers
