"""Thales Careers scraper — uses the Phenom People API."""

import requests
from scrapers.base import BaseScraper


class ThalesScraper(BaseScraper):
    SOURCE_NAME = "thales"

    SEARCH_URL = "https://careers.thalesgroup.com/widgets/search-results"
    PARAMS = {
        "refNum": "TGPTGWGLOBAL",
        "locale": "en_GLOBAL",
        "deviceType": "desktop",
        "siteType": "external",
    }
    PAYLOAD = {
        "appliedFacets": {},
        "limit": 50,
        "offset": 0,
        "searchText": "CIFRE",
    }

    def scrape(self) -> list[dict]:
        try:
            resp = requests.post(
                self.SEARCH_URL,
                params=self.PARAMS,
                json=self.PAYLOAD,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[thales] API request failed: {e}")
            return []

        jobs = data.get("data", {}).get("jobs", [])
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

            # Apply URL if available
            apply_url = job.get("applyUrl", "")

            offers.append({
                "title": title,
                "company": "Thales",
                "description": description,
                "link": apply_url or link,
            })

        print(f"[thales] Found {len(offers)} offers")
        return offers
