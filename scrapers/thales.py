"""Thales Careers scraper — parses embedded DDO data from the Phenom People platform."""

import json
import re

import requests
from scrapers.base import BaseScraper


class ThalesScraper(BaseScraper):
    SOURCE_NAME = "thales"

    SEARCH_URL = "https://careers.thalesgroup.com/global/en/search-results"

    def scrape(self) -> list[dict]:
        try:
            resp = requests.get(
                self.SEARCH_URL,
                params={"keywords": "CIFRE"},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"
                    ),
                },
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[thales] Page request failed: {e}")
            return []

        # The Phenom People platform embeds job data in the page as
        # phApp.ddo = { ... eagerLoadRefineSearch: { ... data: { jobs: [...] } } }
        # Extract the phApp.ddo JSON from the <script> tag.
        html = resp.text
        match = re.search(r"phApp\.ddo\s*=\s*(\{.+?\});\s*(?:phApp\.|var |//|/\*|<)", html, re.DOTALL)
        if not match:
            print("[thales] Could not find phApp.ddo in page HTML")
            return []

        try:
            ddo = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"[thales] Failed to parse phApp.ddo JSON: {e}")
            return []

        # Job data lives under eagerLoadRefineSearch → data → jobs
        jobs = (
            ddo.get("eagerLoadRefineSearch", {})
            .get("data", {})
            .get("jobs", [])
        )

        offers = []
        for job in jobs:
            title = self._clean(job.get("title", ""))
            description = self._clean(
                job.get("descriptionTeaser", "")
                or job.get("ml_job_parser", {}).get("descriptionTeaser", "")
            )
            job_id = job.get("jobId", "")
            slug = title.replace(" ", "-").lower()
            link = f"https://careers.thalesgroup.com/global/en/job/{job_id}/{slug}"

            # Use the direct apply URL if available
            apply_url = job.get("applyUrl", "")

            offers.append({
                "title": title,
                "company": "Thales",
                "description": description,
                "link": apply_url or link,
            })

        print(f"[thales] Found {len(offers)} offers")
        return offers
