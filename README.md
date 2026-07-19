# CIFRE PhD Offers Scraper & Manager

A robust, multi-source scraper and management interface designed to find, filter, and track **CIFRE PhD thesis opportunities** in France.

## 🚀 Key Features

* **11 Multi-Source Scrapers**: Automated scrapers targetting specific job boards and recruiters:
  * **PHD Platform (Doctorat.gouv.fr)**: Playwright-based search and details crawler.
  * **EDF**: Custom WebKit-based bypass for Akamai WAF.
  * **Safran**: Playwright stealth mode bypass for Cloudflare protection.
  * **CEA**: ASP.NET WebForms search submit integration and query pagination.
  * **Orange**, **Airbus**, **Renault**, **Thales**, **INRIA**.
  * **HelloWork**, **LinkedIn**: Skip redundant listings automatically.
* **Smart Filtering & Deduplication**: Offers are hashed deterministically and matched against configurations (allowed tags, keywords, etc.) to skip duplicates.
* **Interactive Web Dashboard**:
  * View offer titles, locations, companies, and **full job descriptions**.
  * Filter by source type and search keywords.
  * Mark offers as **Applied** or **Not Interested** (automatically hides/persists selections).
  * Run scrapers directly from the UI.

---

## 🛠️ Tech Stack

* **Backend**: Python 3, Flask, Playwright (Sync API), BeautifulSoup4.
* **Frontend**: HTML5, Modern Vanilla CSS (Sleek dark mode/glassmorphism theme), Vanilla JS.

---

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/cifre_scraper.git
   cd cifre_scraper
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Configuration**:
   Copy the example config and fill in any credentials:
   ```bash
   cp config.json.example config.json
   ```

---

## 🏃 Running the Application

### 1. Run Scrapers
To run all active scrapers manually and populate the local database:
```bash
python scrape.py
```

### 2. Start Dashboard Server
To start the web dashboard (runs locally on port `5000` by default):
```bash
python server.py
```
Open [http://localhost:5000](http://localhost:5000) in your web browser.

---

## 🔒 Security & Credentials

This repository is pre-configured with a `.gitignore` to prevent committing configuration credentials or temporary files. Ensure `config.json` and `data/offers.json` are **never** committed to version control.
