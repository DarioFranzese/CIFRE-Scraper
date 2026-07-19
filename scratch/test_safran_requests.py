import requests
from bs4 import BeautifulSoup

url = "https://www.safran-group.com/jobs?search=cifre"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Response Status:", response.status_code)
    print("Response headers:", response.headers)
    soup = BeautifulSoup(response.text, "html.parser")
    print("Page Title:", soup.title.string if soup.title else "No title")
    print("Body length:", len(response.text))
    # search for .c-offer-item
    items = soup.find_all(class_="c-offer-item")
    print(f"Found {len(items)} .c-offer-item in requests HTML")
    for i, item in enumerate(items[:2]):
        print(f"Item {i}:", item.prettify()[:500])
except Exception as e:
    print("Error:", e)
