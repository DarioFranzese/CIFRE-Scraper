"""Orange Jobs scraper — uses the Phenom People API (JSON embedded in page)."""

import json
import requests
from scrapers.base import BaseScraper


class OrangeScraper(BaseScraper):
    SOURCE_NAME = "orange"

    SEARCH_URL = "https://orange.jobs/widgets/search-results"
    PARAMS = {
        "refNum": "OYVOCZGB",
        "locale": "en_GB",
        "deviceType": "desktop",
        "siteType": "external",
    }
    PAYLOAD = {
        "appliedFacets": {},
        "limit": 50,
        "offset": 0,
        "searchText": "phd",
    }

    def scrape(self) -> list[dict]:
        title_keywords = [kw.lower() for kw in self.config.get("orange", {}).get(
            "title_must_contain", ["PhD", "Thèse", "These", "Doctorat"]
        )]

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
            print(f"[orange] API request failed: {e}")
            return []

        jobs = data.get("data", {}).get("jobs", [])
        offers = []
        for job in jobs:
            title = self._clean(job.get("title", ""))
            # Filter: title must contain PhD / Thèse / etc.
            if not any(kw in title.lower() for kw in title_keywords):
                continue

            description = self._clean(
                job.get("descriptionTeaser", "")
                or job.get("ml_job_parser", {}).get("descriptionTeaser", "")
            )
            job_id = job.get("jobId", "")
            # Build link to individual job page
            link = f"https://orange.jobs/gb/en/job/{job_id}/{title.replace(' ', '-').lower()}"

            offers.append({
                "title": title,
                "company": self._clean(job.get("company", "Orange")),
                "description": description,
                "link": link,
            })

        print(f"[orange] Found {len(offers)} offers")
        return offers
