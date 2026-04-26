import cloudscraper
from bs4 import BeautifulSoup
import json, csv, time, os
from datetime import datetime

def scrape_harga():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/IONQ?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    res = scraper.get(url, headers=headers)
    data = res.json()
    try:
        harga = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        # Validasi: harga IONQ wajar antara $1 - $500
        if 1 < harga < 500:
            return float(harga)
        else:
            return None
    except:
        return None

def scrape_historis():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/IONQ?interval=1d&range=30d"
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    res = scraper.get(url, headers=headers)
    data = res.json()
    hasil = []
    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        for t, c in zip(timestamps, closes):
            tanggal = datetime.fromtimestamp(t).strftime("%Y-%m-%d")
            hasil.append({"tanggal": tanggal, "close": round(c, 2)})
    except:
        pass
    return hasil

def simpan_csv(harga, filename="ionq_realtime.csv"):
    file_baru = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if file_baru:
            writer.writerow(["Waktu", "Harga"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), harga])

def cek_notifikasi(harga, harga_sebelumnya, threshold=2.0):
    if harga_sebelumnya is None:
        return
    selisih = harga - harga_sebelumnya
    persen = (selisih / harga_sebelumnya) * 100
    if abs(persen) >= threshold:
        arah = "NAIK 🚀" if persen > 0 else "TURUN 🔻"
        print(f"\n⚠️  ALERT! Harga {arah}")
        print(f"   {harga_sebelumnya} → {harga} ({persen:+.2f}%)\n")

def tampilkan_historis(data):
    print("\n📊 Historis 30 Hari Terakhir:")
    print(f"{'Tanggal':<15} {'Harga':>10}")
    print("-" * 27)
    for d in data[-10:]:  # tampilkan 10 terakhir
        print(f"{d['tanggal']:<15} ${d['close']:>9.2f}")

    # Simpan ke CSV
    with open("ionq_historis.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Tanggal", "Harga Close"])
        for d in data:
            writer.writerow([d["tanggal"], d["close"]])
    print("Tersimpan: ionq_historis.csv")

# ── MAIN ──
print("=" * 40)
print("  IONQ Monitor - Yahoo Finance")
print("=" * 40)

# Ambil & tampilkan historis dulu
print("\n⏳ Mengambil data historis...")
historis = scrape_historis()
if historis:
    tampilkan_historis(historis)
else:
    print("Gagal ambil data historis.")

# Auto scrape realtime tiap 60 detik
INTERVAL = 60        # detik
THRESHOLD = 2.0      # persen untuk notifikasi
harga_sebelumnya = None

print(f"\n🔄 Mulai monitoring harga tiap {INTERVAL} detik...")
print("Tekan CTRL+C untuk berhenti\n")

while True:
    try:
        waktu = datetime.now().strftime("%H:%M:%S")
        harga = scrape_harga()

        if harga:
            cek_notifikasi(harga, harga_sebelumnya, THRESHOLD)
            simpan_csv(harga)
            print(f"[{waktu}] Harga IONQ: ${harga:.2f}", end="")
            if harga_sebelumnya:
                selisih = harga - harga_sebelumnya
                print(f"  ({selisih:+.2f})", end="")
            print()
            harga_sebelumnya = harga
        else:
            print(f"[{waktu}] Gagal ambil harga, mencoba lagi...")

        time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n\nMonitoring dihentikan.")
        print("Data tersimpan di: ionq_realtime.csv & ionq_historis.csv")
        break
