"""Test Orange pagination - different URL patterns."""
import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def extract_jobs(html):
    match = re.search(r'"eagerLoadRefineSearch"\s*:\s*\{', html)
    if not match:
        return None, 0
    json_start = html.index("{", match.start() + len('"eagerLoadRefineSearch":'))
    brace_count = 0
    i = json_start
    while i < len(html):
        if html[i] == "{": brace_count += 1
        elif html[i] == "}":
            brace_count -= 1
            if brace_count == 0: break
        i += 1
    data = json.loads(html[json_start:i+1])
    return data.get("data", {}).get("jobs", []), data.get("totalHits", 0)

urls = [
    ("keywords only", "https://orange.jobs/gb/en/search-results?keywords=phd"),
    ("keywords + from=0", "https://orange.jobs/gb/en/search-results?keywords=phd&from=0"),
    ("keywords + from=0 + s=1", "https://orange.jobs/gb/en/search-results?keywords=phd&from=0&s=1"),
    ("keywords + from=10", "https://orange.jobs/gb/en/search-results?keywords=phd&from=10"),
    ("from=10 + s=1 (no keywords)", "https://orange.jobs/gb/en/search-results?from=10&s=1"),
]

for label, url in urls:
    print(f"\n=== {label} ===")
    resp = requests.get(url, headers=headers, timeout=15)
    jobs, total = extract_jobs(resp.text)
    if jobs is not None:
        print(f"  totalHits: {total}, jobs: {len(jobs)}")
        for j in jobs[:3]:
            t = j.get("title", "")
            tl = t.lower()
            match_kw = any(k in tl for k in ["phd", "thesis", "thèse"])
            print(f"  {'V' if match_kw else 'X'} {t}")
        if len(jobs) > 3:
            print(f"  ... and {len(jobs) - 3} more")
    else:
        print("  No data found")
