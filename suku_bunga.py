import cloudscraper
from bs4 import BeautifulSoup
import json, csv, time, os
from datetime import datetime

def scrape_semua():
    scraper = cloudscraper.create_scraper()
    headers = {"User-Agent": "Mozilla/5.0"}
    hasil = {}

    # Sumber 1: Wikipedia - List of countries by central bank interest rates
    try:
        print("  Mencoba Wikipedia...")
        url = "https://en.wikipedia.org/wiki/List_of_countries_by_central_bank_interest_rates"
        res = scraper.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        tabel = soup.find("table", {"class": "wikitable"})
        if tabel:
            rows = tabel.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all(["td", "th"])
                if len(cols) >= 2:
                    negara = cols[0].text.strip()
                    rate_text = cols[1].text.strip().replace("%","").replace("−","-").strip()
                    try:
                        rate = float(rate_text)
                        if negara:
                            hasil[negara] = rate
                    except:
                        pass
        print(f"  Wikipedia: {len(hasil)} negara")
    except Exception as e:
        print(f"  Wikipedia gagal: {e}")

    # Sumber 2: countryeconomy.com
    if len(hasil) < 50:
        try:
            print("  Mencoba countryeconomy.com...")
            url = "https://countryeconomy.com/key-rates"
            res = scraper.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            tabel = soup.find("table")
            if tabel:
                rows = tabel.find_all("tr")[1:]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        negara = cols[0].text.strip()
                        rate_text = cols[1].text.strip().replace("%","").replace(",",".").strip()
                        try:
                            rate = float(rate_text)
                            if negara and negara not in hasil:
                                hasil[negara] = rate
                        except:
                            pass
            print(f"  countryeconomy.com: {len(hasil)} negara")
        except Exception as e:
            print(f"  countryeconomy gagal: {e}")

    # Sumber 3: globalrates.com
    if len(hasil) < 80:
        try:
            print("  Mencoba globalrates.com...")
            url = "https://www.globalrates.com/interest-rates/central-bank-interest-rate/central-bank-interest-rate.aspx"
            res = scraper.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            tabel = soup.find("table")
            if tabel:
                rows = tabel.find_all("tr")[1:]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        negara = cols[0].text.strip()
                        rate_text = cols[1].text.strip().replace("%","").replace(",",".").strip()
                        try:
                            rate = float(rate_text)
                            if negara and negara not in hasil:
                                hasil[negara] = rate
                        except:
                            pass
            print(f"  globalrates.com: {len(hasil)} negara")
        except Exception as e:
            print(f"  globalrates gagal: {e}")

    return hasil

def load_sebelumnya(filename="suku_bunga_history.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def simpan_sekarang(data, filename="suku_bunga_history.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def simpan_csv(perubahan, waktu):
    filename = f"suku_bunga_{datetime.now().strftime('%Y%m%d')}.csv"
    file_baru = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if file_baru:
            writer.writerow(["Waktu","Negara","Sebelumnya","Sekarang","Perubahan","Status"])
        for p in perubahan:
            writer.writerow([waktu, p["negara"], p["sebelumnya"],
                           p["sekarang"], p["perubahan"], p["status"]])
    return filename

def cek_perubahan(lama, baru):
    perubahan = []
    for negara, bunga_baru in baru.items():
        if negara in lama:
            bunga_lama = lama[negara]
            if bunga_baru != bunga_lama:
                selisih = bunga_baru - bunga_lama
                perubahan.append({
                    "negara": negara,
                    "sebelumnya": bunga_lama,
                    "sekarang": bunga_baru,
                    "perubahan": round(selisih, 4),
                    "status": "NAIK 🚀" if selisih > 0 else "TURUN 🔻"
                })
    return perubahan

def tampilkan_semua(data, perubahan, waktu):
    os.system("clear")
    print("=" * 60)
    print(f"  🌍 GLOBAL INTEREST RATE MONITOR")
    print(f"  Update: {waktu}")
    print(f"  Total negara: {len(data)}")
    print("=" * 60)

    if perubahan:
        print(f"\n🔔 PERUBAHAN TERDETEKSI ({len(perubahan)} negara):")
        print("-" * 60)
        print(f"{'Negara':<25} {'Lama':>7} {'Baru':>7} {'Selisih':>10} Status")
        print("-" * 60)
        for p in perubahan:
            print(f"{p['negara']:<25} {p['sebelumnya']:>6.2f}% "
                  f"{p['sekarang']:>6.2f}% "
                  f"{p['perubahan']:>+9.4f}% "
                  f"{p['status']}")
    else:
        print("\n✅ Tidak ada perubahan suku bunga")

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    print(f"\n📊 TOP 10 TERTINGGI:")
    print(f"{'Negara':<25} {'Rate':>8}")
    print("-" * 35)
    for negara, rate in sorted_data[:10]:
        print(f"{negara:<25} {rate:>7.2f}%")

    print(f"\n📊 TOP 10 TERENDAH:")
    print(f"{'Negara':<25} {'Rate':>8}")
    print("-" * 35)
    for negara, rate in sorted_data[-10:]:
        print(f"{negara:<25} {rate:>7.2f}%")

    penting = ["United States","Euro Area","United Kingdom",
               "Japan","China","Indonesia","Australia","Canada",
               "India","Brazil","Russia","South Korea"]
    print(f"\n🌐 NEGARA PENTING:")
    print(f"{'Negara':<25} {'Rate':>8}")
    print("-" * 35)
    for n in penting:
        if n in data:
            print(f"{n:<25} {data[n]:>7.2f}%")

    print(f"\n{'='*60}")
    print(f"Update berikutnya: 1 jam | CTRL+C berhenti")

# ── MAIN ──
print("=" * 60)
print("  🌍 GLOBAL INTEREST RATE MONITOR")
print("  Multi-source scraping...")
print("=" * 60)

while True:
    try:
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏳ [{waktu}] Mengambil data...")

        data_baru = scrape_semua()

        if not data_baru:
            print("❌ Gagal, retry 5 menit...")
            time.sleep(300)
            continue

        print(f"✅ Total: {len(data_baru)} negara")

        data_lama = load_sebelumnya()
        perubahan = cek_perubahan(data_lama, data_baru)
        simpan_sekarang(data_baru)
        tampilkan_semua(data_baru, perubahan, waktu)

        if perubahan:
            filename = simpan_csv(perubahan, waktu)
            print(f"📁 Tersimpan: {filename}")

        time.sleep(3600)

    except KeyboardInterrupt:
        print("\n\nMonitoring dihentikan.")
        break
    except Exception as e:
        print(f"Error: {e}, retry 5 menit...")
        time.sleep(300)
