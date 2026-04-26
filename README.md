# 🌍 Global Interest Rate Monitor

A Python script that automatically monitors central bank interest rates from countries around the world in real-time.

## Features

- **Multi-source scraping** — fetches data from Wikipedia, countryeconomy.com, and globalrates.com
- **Change detection** — instant notification when any country raises or cuts its rate
- **Hourly updates** — runs continuously in the background
- **Daily CSV export** — saves change history to a dated CSV file
- **Clean summary view** — Top 10 highest, Top 10 lowest, and key global economies

## Countries Covered

80+ countries including:
- 🇺🇸 United States · 🇪🇺 Euro Area · 🇬🇧 United Kingdom
- 🇯🇵 Japan · 🇨🇳 China · 🇮🇩 Indonesia
- 🇦🇺 Australia · 🇨🇦 Canada · 🇮🇳 India · 🇧🇷 Brazil

## Installation

```bash
pip install cloudscraper beautifulsoup4
```

## Usage

```bash
python suku_bunga.py
```

Press `CTRL+C` to stop monitoring.

## Output Files

| File | Description |
|------|-------------|
| `suku_bunga_history.json` | Latest interest rate data for all countries |
| `suku_bunga_YYYYMMDD.csv` | Daily log of detected changes |

## Sample Output

```
============================================================
  🌍 GLOBAL INTEREST RATE MONITOR
  Update: 2026-04-26 22:30:00
  Total countries: 85
============================================================

🔔 CHANGES DETECTED (1 country):
Country                   Before    Now     Change   Status
United States             5.50%   5.25%   -0.2500%  TURUN 🔻

📊 TOP 10 HIGHEST:
Argentina               97.00%
...
```

## Tech Stack

- `cloudscraper` — bypasses Cloudflare protection
- `BeautifulSoup4` — HTML parsing
- `json` + `csv` — local data storage

## License

MIT
