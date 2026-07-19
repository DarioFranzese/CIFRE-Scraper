"""Renault Jobs scraper — Workday SPA, uses JSON API."""

import requests
from scrapers.base import BaseScraper


class RenaultScraper(BaseScraper):
    SOURCE_NAME = "renault"

    API_URL = "https://alliancewd.wd3.myworkdayjobs.com/wday/cxs/alliancewd/renault-group-careers/jobs"

    def scrape(self) -> list[dict]:
        try:
            resp = requests.post(
                self.API_URL,
                json={
                    "appliedFacets": {},
                    "limit": 20,
                    "offset": 0,
                    "searchText": "CIFRE",
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[renault] API request failed: {e}")
            return []

        job_postings = data.get("jobPostings", [])
        offers = []
        for job in job_postings:
            title = self._clean(job.get("title", ""))
            external_path = job.get("externalPath", "")
            link = f"https://alliancewd.wd3.myworkdayjobs.com/en-US/renault-group-careers{external_path}" if external_path else ""

            bullets = job.get("bulletFields", [])
            location = bullets[0] if bullets else ""
            posted = bullets[1] if len(bullets) > 1 else ""
            description = f"Location: {location}. Posted: {posted}" if location else ""

            offers.append({
                "title": title,
                "company": "Renault",
                "description": self._clean(description),
                "link": link,
            })

        print(f"[renault] Found {len(offers)} offers")
        return offers
