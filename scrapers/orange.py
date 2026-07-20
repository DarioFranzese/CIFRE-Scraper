"""Orange Jobs scraper — extracts job data from embedded JSON in the search page."""

import json
import re
import requests
from scrapers.base import BaseScraper


class OrangeScraper(BaseScraper):
    SOURCE_NAME = "orange"

    SEARCH_URL = "https://orange.jobs/gb/en/search-results"
    BASE_URL = "https://orange.jobs"
    PAGE_SIZE = 10  # Orange returns 10 results per page

    # Keywords the title must contain (lowercased for matching)
    TITLE_KEYWORDS = ["phd", "thesis", "thèse"]

    def scrape(self) -> list[dict]:
        title_keywords = [kw.lower() for kw in self.config.get("orange", {}).get(
            "title_must_contain", self.TITLE_KEYWORDS
        )]

        # Fetch all pages of results
        all_jobs = []
        offset = 0
        total_hits = None

        while True:
            jobs, total_hits = self._fetch_page(offset)
            if jobs is None or len(jobs) == 0:
                break
            all_jobs.extend(jobs)
            offset += self.PAGE_SIZE
            if offset >= total_hits:
                break

        print(f"[orange] Fetched {len(all_jobs)} raw jobs across {(offset // self.PAGE_SIZE)} page(s) (totalHits: {total_hits})")

        # Filter by title keywords
        offers = []
        for job in all_jobs:
            title = self._clean(job.get("title", ""))
            title_lower = title.lower()
            if not any(kw in title_lower for kw in title_keywords):
                continue

            description = self._clean(
                job.get("descriptionTeaser", "")
                or job.get("ml_job_parser", {}).get("descriptionTeaser", "")
            )
            job_id = job.get("jobId", "")
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            link = f"{self.BASE_URL}/gb/en/job/{job_id}/{slug}"

            offers.append({
                "title": title,
                "company": self._clean(job.get("company", "Orange")),
                "description": description or "No description available",
                "link": link,
            })

        print(f"[orange] Found {len(offers)} offers after title filter")
        return offers

    def _fetch_page(self, offset: int = 0) -> tuple[list[dict] | None, int]:
        """Fetch a page of search results by parsing embedded JSON from the HTML.

        The Orange careers site (Phenom People platform) embeds job search data
        in ``phApp.ddo.eagerLoadRefineSearch`` within the server-rendered HTML.

        Pagination uses the ``from`` query parameter (0, 10, 20, …).
        Important: the ``s=1`` parameter must NOT be used as it disables keyword
        filtering and returns all jobs instead.
        """
        params = {"keywords": "phd"}
        if offset > 0:
            params["from"] = str(offset)

        try:
            resp = requests.get(
                self.SEARCH_URL,
                params=params,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html",
                },
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[orange] HTTP request failed: {e}")
            return None, 0

        html = resp.text

        # Locate the eagerLoadRefineSearch JSON object in the page
        pattern = r'"eagerLoadRefineSearch"\s*:\s*\{'
        match = re.search(pattern, html)
        if not match:
            print("[orange] Could not find eagerLoadRefineSearch in page HTML")
            return None, 0

        # Extract the balanced JSON object by counting braces
        json_start = html.index("{", match.start() + len('"eagerLoadRefineSearch":'))
        brace_count = 0
        i = json_start
        while i < len(html):
            if html[i] == "{":
                brace_count += 1
            elif html[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    break
            i += 1

        json_str = html[json_start : i + 1]
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[orange] JSON parse error: {e}")
            return None, 0

        total_hits = data.get("totalHits", 0)
        jobs = data.get("data", {}).get("jobs", [])
        return jobs, total_hits
