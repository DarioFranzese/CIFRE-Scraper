"""STMicroelectronics scraper — scrapes CIFRE PhD offers from Eightfold AI portal."""

import html
import re
from scrapers.base import BaseScraper


class STMicroelectronicsScraper(BaseScraper):
    SOURCE_NAME = "stmicroelectronics"

    DEFAULT_URL = (
        "https://stmicroelectronics.eightfold.ai/careers"
        "?query=CIFRE&location=France&pid=563637171228634&domain=stmicroelectronics.com&sort_by=relevance"
    )

    def scrape(self) -> list[dict]:
        """Scrape CIFRE offers from STMicroelectronics Eightfold portal."""
        cfg = self.config.get("stmicroelectronics", {})
        start_url = cfg.get("url", self.DEFAULT_URL)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[stmicroelectronics] Playwright is not installed.")
            return []

        offers = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            )
            page = context.new_page()
            page.add_init_script("delete navigator.__proto__.webdriver;")

            print(f"[stmicroelectronics] Navigating to: {start_url}")
            page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(".card.position-card", timeout=30000)

            # Step 1: Click "show more positions" until all positions are loaded
            show_more = page.locator(".btn.btn-sm.btn-secondary.show-more-positions")
            clicks = 0
            while show_more.count() > 0 and show_more.is_visible():
                clicks += 1
                print(f"[stmicroelectronics] Loading more positions (click #{clicks})...")
                show_more.first.click()
                page.wait_for_timeout(2000)
                show_more = page.locator(".btn.btn-sm.btn-secondary.show-more-positions")

            cards = page.locator(".card.position-card")
            card_count = cards.count()
            print(f"[stmicroelectronics] Loaded {card_count} total cards. Extracting CIFRE positions...")

            seen_titles = set()

            for i in range(card_count):
                card = cards.nth(i)
                card_text = card.inner_text().strip()
                lines = [line.strip() for line in card_text.split("\n") if line.strip()]
                title = lines[0] if lines else ""

                # Only include CIFRE offers
                if "cifre" not in title.lower():
                    continue

                # Deduplicate repeated cards by normalized title
                norm_title = self._clean(title).lower()
                if norm_title in seen_titles:
                    continue
                seen_titles.add(norm_title)

                # Step 2: Simulate clicking the card to load its details into the side container
                try:
                    card.scroll_into_view_if_needed()
                    card.dispatch_event("click")
                    page.wait_for_timeout(1000)
                    page.wait_for_selector(
                        ".position-container .position-job-description",
                        timeout=10000,
                    )

                    offer_link = page.url
                    desc_el = page.locator(".position-job-description").first
                    description = self._extract_formatted_description(desc_el)

                    offers.append({
                        "title": title,
                        "company": "STMicroelectronics",
                        "description": description,
                        "link": offer_link,
                    })
                    print(f"[stmicroelectronics] Scraped [{len(offers)}]: {title}")

                except Exception as e:
                    print(f"[stmicroelectronics] Error extracting details for '{title}': {e}")

            browser.close()

        print(f"[stmicroelectronics] Completed scraping: {len(offers)} offers extracted.")
        return offers

    def _extract_formatted_description(self, desc_locator) -> str:
        """Extract description while maintaining formatting across nested div/p/li blocks."""
        try:
            # Evaluate script in page context to convert HTML blocks into clean, structured formatted text
            formatted_text = desc_locator.evaluate("""el => {
                // Clone node to avoid modifying live page
                const clone = el.cloneNode(true);

                // Add newline breaks before block-level elements
                const blockTags = ['DIV', 'P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'LI', 'BR'];
                const walker = document.createTreeWalker(clone, NodeFilter.SHOW_ELEMENT, null, false);
                const nodes = [];
                while (walker.nextNode()) {
                    nodes.push(walker.currentNode);
                }

                nodes.forEach(node => {
                    if (node.tagName === 'LI') {
                        node.prepend('• ');
                    }
                });

                return clone.innerText || '';
            }""")
            return self._clean_formatted(formatted_text)
        except Exception:
            # Fallback to inner_text
            return self._clean_formatted(desc_locator.inner_text())

    @staticmethod
    def _clean_formatted(text: str) -> str:
        """Clean extra blank lines while preserving paragraph and bullet line breaks."""
        if not text:
            return ""
        # Decode HTML entities if any
        text = html.unescape(text)
        # Normalize multiple line breaks to maximum two
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        last_empty = False
        for line in lines:
            if not line:
                if not last_empty:
                    cleaned_lines.append("")
                    last_empty = True
            else:
                cleaned_lines.append(line)
                last_empty = False
        return "\n".join(cleaned_lines).strip()


if __name__ == "__main__":
    scraper = STMicroelectronicsScraper()
    results = scraper.run()
    print(f"\nFinal result: {len(results)} offers extracted")
    for r in results:
        print(f"[{r['id']}] {r['title']} | {r['link']}")
