"""Airbus Jobs scraper — Workday SPA, requires Playwright or API."""

import requests
from scrapers.base import BaseScraper


class AirbusScraper(BaseScraper):
    SOURCE_NAME = "airbus"

    # Workday has a JSON API we can call directly
    API_URL = "https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/Airbus/jobs"

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
            print(f"[airbus] API request failed: {e}")
            return []

        job_postings = data.get("jobPostings", [])
        offers = []
        for job in job_postings:
            title = self._clean(job.get("title", ""))
            # Build the detail link
            external_path = job.get("externalPath", "")
            link = f"https://ag.wd3.myworkdayjobs.com/en-US/Airbus{external_path}" if external_path else ""

            # Get bullet points / teaser
            bullets = job.get("bulletFields", [])
            location = ""
            posted = ""
            for bullet in bullets:
                if "postedOn" in str(bullet).lower():
                    posted = bullet
                else:
                    location = bullet

            description = f"Location: {location}. Posted: {posted}" if location else ""

            offers.append({
                "title": title,
                "company": "Airbus",
                "description": self._clean(description),
                "link": link,
            })

        print(f"[airbus] Found {len(offers)} offers")
        return offers
