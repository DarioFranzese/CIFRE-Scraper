# 🎓 CIFRE PhD Offers Scraper & Manager

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated-orange.svg)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

A robust, multi-source scraping orchestrator and management dashboard designed to discover, filter, and track **CIFRE PhD thesis opportunities** (*Conventions Industrielles de Formation par la Recherche*) in France.

---

## 🚀 Key Features

* **12 Automated Multi-Source Scrapers**:
  * 🏛️ **Doctorat.gouv.fr**: Official French national PhD portal crawler (Playwright search & details parser).
  * ⚡ **EDF**: Custom WebKit browser rendering bypass for Akamai WAF protection.
  * ✈️ **Safran**: Playwright stealth mode bypass for Cloudflare anti-bot security.
  * 🏭 **Aubert & Duval**: Form POST filtering for specific contract types ("Thèse – CIFRE").
  * ⚛️ **CEA**: ASP.NET WebForms session tracking and query pagination.
  * 🌐 **Airbus & Renault**: Direct Workday REST API search integrations.
  * 📡 **Orange, Thales, INRIA**: Specialized corporate and research job board scrapers.
  * 🔍 **HelloWork**: Aggregator scraping with automated duplicate suppression.
  * 💼 **France Travail**: National employment portal with dynamic Playwright pagination & microdata extraction.
* **Smart Filtering & Deduplication**:
  * Deterministic SHA-256 offer hashing to prevent duplicate entries across scrapes.
  * Configurable filtering rules (allowed tags, required title keywords, date ranges).
  * Skip company listings on aggregator sites if directly scraped.
* **Interactive Web Dashboard**:
  * Modern dark-mode UI with glassmorphism styling.
  * View position titles, hiring company, location, date found, and full job descriptions.
  * Filter by source portal and search keywords in real time.
  * Application tracking lifecycle: Mark offers as **Applied** or **Not Interested** (persists across sessions).
  * One-click manual background scrape trigger directly from the web interface.

---

## 📂 Project Architecture

```text
cifre_scraper/
├── config.json.example   # Template configuration file
├── scrape.py             # CLI scraping orchestrator
├── server.py             # Flask Web UI server & REST API
├── data/                 # Data storage directory
│   ├── README.md         # Schema & offer lifecycle documentation
│   └── offers.json       # Local database (gitignored)
├── scrapers/             # Scraper modules subfolder
│   ├── README.md         # Scraper architecture & developer guide
│   ├── base.py           # Abstract BaseScraper class
│   ├── doctorat_gouv.py  # Doctorat.gouv.fr scraper
│   ├── safran.py         # Safran careers scraper
│   ├── aubertduval.py    # Aubert & Duval careers scraper
│   ├── airbus.py         # Airbus Workday API scraper
│   ├── renault.py        # Renault Workday API scraper
│   ├── cea.py            # CEA ASP.NET scraper
│   ├── edf.py            # EDF WebKit scraper
│   ├── orange.py         # Orange API scraper
│   ├── thales.py         # Thales scraper
│   ├── inria.py          # INRIA scraper
│   ├── hellowork.py      # HelloWork aggregator scraper
│   └── francetravail.py  # France Travail scraper
└── static/               # Frontend web app assets
    ├── index.html        # Web dashboard layout
    ├── style.css         # Custom CSS theme
    └── app.js            # Frontend REST API interaction logic
```

For detailed architecture breakdowns:
- 📖 Read the [**Scrapers Documentation**](scrapers/README.md) to learn how individual scrapers work or how to write a new scraper.
- 📖 Read the [**Data Schema Documentation**](data/README.md) to understand the storage format and status lifecycle.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- `pip` and `venv` package managers

### 2. Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/cifre_scraper.git
   cd cifre_scraper
   ```

2. **Create and activate a virtual environment**:
   - **Windows**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Python dependencies and Playwright browsers**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Set up configuration**:
   Copy the example configuration file and customize your search criteria:
   ```bash
   cp config.json.example config.json
   ```

---

## 🏃 Usage

### 1. Run Scrapers via CLI
Execute all active scrapers manually from the terminal to populate or refresh `data/offers.json`:
```bash
python scrape.py
```

### 2. Start Web Dashboard Server
Launch the Flask development server:
```bash
python server.py
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🌐 REST API Endpoints

The Flask server provides the following endpoints for integration:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/offers` | Fetch stored offers (supports `?source=`, `?status=`, and `?search=` filters). |
| `POST` | `/api/offers/<offer_id>/status` | Update tracking status (`new`, `seen`, `applied`, `not_interested`). |
| `POST` | `/api/refresh` | Trigger an asynchronous background scrape run. |
| `GET` | `/api/status` | Check background scraping status and execution results. |

---

## 🔒 Security & Privacy Notice

> [!IMPORTANT]
> The `.gitignore` file is pre-configured to exclude `config.json` and `data/offers.json`.
>
> - **`config.json`**: May contain portal credentials or private search criteria. Always keep real passwords out of Git repositories.
> - **`data/offers.json`**: Contains your personal application tracking status and local job search history.
