'EOF'
"""
Monitor Harga Saham Watchlist
- Sumber harga: Yahoo Finance
- Kurs USD/IDR: auto fetch
- Library: requests saja (tanpa yfinance/pandas)
"""

import requests
import time
from datetime import datetime

# =============================================
# KONFIGURASI WATCHLIST
# =============================================
WATCHLIST = {
    "AAPL":  "Apple",
    "MU":    "Micron Technology",
    "STX":   "Seagate Technology",
    "PLTR":  "Palantir",
    "ASML":  "ASML",
    "MSFT":  "Microsoft",
    "IONQ":  "IonQ Inc",
    "NVDA":  "NVIDIA",
    "GOOGL": "Google",
    "AMZN":  "Amazon",
    "AVGO":  "Broadcom",
}

ALERT_THRESHOLD_PERCENT = 3.0
REFRESH_INTERVAL = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

session = requests.Session()
session.headers.update(HEADERS)


# =============================================
# AMBIL COOKIE + CRUMB
# =============================================

def get_crumb():
    try:
        session.get("https://finance.yahoo.com", timeout=10)
        r = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10)
        crumb = r.text.strip()
        if crumb and len(crumb) > 3:
            return crumb
        return None
    except Exception as e:
        print(f"  [!] Gagal ambil crumb: {e}")
        return None


def get_yahoo_price(symbols, crumb):
    all_symbols = symbols + ["USDIDR=X"]
    symbols_str = ",".join(all_symbols)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols_str}&crumb={crumb}"

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        quotes = data["quoteResponse"]["result"]

        result = {}
        for quote in quotes:
            symbol = quote.get("symbol")
            result[symbol] = {
                "price": quote.get("regularMarketPrice", 0),
                "prev_close": quote.get("regularMarketPreviousClose", 0),
                "change_pct": quote.get("regularMarketChangePercent", 0),
            }
        return result

    except Exception as e:
        print(f"  [!] Gagal fetch data: {e}")
        return {}


# =============================================
# TAMPILAN
# =============================================

def format_idr(amount):
    return f"Rp{amount:,.0f}".replace(",", ".")

def sep():
    print("  " + "-" * 34)

def print_watchlist(data):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    usd_idr_data = data.get("USDIDR=X")
    usd_idr = usd_idr_data["price"] if usd_idr_data else None
    kurs_str = format_idr(usd_idr) if usd_idr else "N/A"

    print("\n  ================================")
    print(f"  WATCHLIST SAHAM")
    print(f"  {now}")
    print(f"  Kurs: {kurs_str}")
    print("  ================================")

    alerts = []

    for symbol, name in WATCHLIST.items():
        quote = data.get(symbol)
        sep()
        if not quote:
            print(f"  {symbol} {name}")
            print(f"  Data tidak tersedia")
            continue

        price_usd  = quote["price"]
        change_pct = quote["change_pct"]
        price_idr  = price_usd * usd_idr if usd_idr else None

        usd_str = f"${price_usd:,.2f}"
        idr_str = format_idr(price_idr) if price_idr else "N/A"

        if change_pct > 0:
            arrow = "▲"
            change_str = f"▲ +{change_pct:.2f}%"
        elif change_pct < 0:
            arrow = "▼"
            change_str = f"▼ {change_pct:.2f}%"
        else:
            arrow = "─"
            change_str = f"─  {change_pct:.2f}%"

        alert_str = ""
        if abs(change_pct) >= ALERT_THRESHOLD_PERCENT:
            direction = "NAIK" if change_pct > 0 else "TURUN"
            alert_str = f"  ⚠ {direction}"
            alerts.append((symbol, name, change_pct, direction))

        # Baris 1: ticker + nama
        print(f"  {symbol:<5} {name}")
        # Baris 2: harga USD + IDR + change + alert
        print(f"  {usd_str:<10} {idr_str:<16} {change_str}{alert_str}")

    sep()
    print("  ================================")

    # Ringkasan alert
    if alerts:
        print(f"\n  ⚠ ALERT (>= {ALERT_THRESHOLD_PERCENT}%):")
        for sym, nm, pct, direction in alerts:
            sign = "+" if pct > 0 else ""
            print(f"  • {sym} {direction} {sign}{pct:.2f}%")
    else:
        print(f"\n  ✓ Tidak ada alert")

    print(f"\n  Refresh dalam {REFRESH_INTERVAL}s... (Ctrl+C stop)\n")


# =============================================
# MAIN
# =============================================

def main():
    print("\n  Memulai monitor watchlist saham...")
    print(f"  Saham: {', '.join(WATCHLIST.keys())}")
    print(f"  Alert threshold: {ALERT_THRESHOLD_PERCENT}%")
    print(f"  Refresh interval: {REFRESH_INTERVAL} detik")

    print("\n  Mengambil session Yahoo Finance...")
    crumb = get_crumb()
    if not crumb:
        print("  [!] Gagal ambil crumb. Coba lagi nanti.")
        return
    print(f"  Session OK (crumb: {crumb[:6]}...)")

    while True:
        try:
            print("\n  Fetching data...")
            data = get_yahoo_price(list(WATCHLIST.keys()), crumb)
            print_watchlist(data)
            time.sleep(REFRESH_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n  Monitor dihentikan. Sampai jumpa!\n")
            break
        except Exception as e:
            print(f"\n  [!] Error: {e}")
            print("  Refresh crumb...")
            crumb = get_crumb() or crumb
            time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()

EOF
