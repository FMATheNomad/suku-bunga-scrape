import cloudscraper
from bs4 import BeautifulSoup
import json, csv, time, os
from datetime import datetime

def jam_pasar():
    now = datetime.now()
    hari = now.weekday()  # 0=Senin, 6=Minggu
    jam = now.hour
    menit = now.minute

    # Cek hari kerja
    if hari >= 5:  # Sabtu/Minggu
        return False, "Tutup (Weekend)"

    waktu = jam * 60 + menit  # dalam menit

    sesi1_buka = 9 * 60        # 09:00
    sesi1_tutup = 11 * 60 + 30 # 11:30
    sesi2_buka = 13 * 60 + 30  # 13:30
    sesi2_tutup = 15 * 60 + 49 # 15:49

    if sesi1_buka <= waktu <= sesi1_tutup:
        return True, "Sesi 1 (09:00-11:30)"
    elif sesi2_buka <= waktu <= sesi2_tutup:
        return True, "Sesi 2 (13:30-15:49)"
    elif waktu < sesi1_buka:
        return False, f"Belum buka (buka pukul 09:00)"
    elif sesi1_tutup < waktu < sesi2_buka:
        return False, f"Jeda siang (buka lagi 13:30)"
    else:
        return False, "Sudah tutup (buka besok 09:00)"

def scrape_harga():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/BBCA.JK?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    res = scraper.get(url, headers=headers)
    data = res.json()
    try:
        harga = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        if 1000 < harga < 100000:
            return float(harga)
        return None
    except:
        return None

def scrape_historis():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/BBCA.JK?interval=1d&range=30d"
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    res = scraper.get(url, headers=headers)
    data = res.json()
    hasil = []
    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        for t, c in zip(timestamps, closes):
            if c:
                tanggal = datetime.fromtimestamp(t).strftime("%Y-%m-%d")
                hasil.append({"tanggal": tanggal, "close": round(c, 2)})
    except:
        pass
    return hasil

def simpan_csv(harga, filename="bbca_realtime.csv"):
    file_baru = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if file_baru:
            writer.writerow(["Waktu", "Harga (IDR)"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), harga])

def cek_notifikasi(harga, harga_sebelumnya, threshold=2.0):
    if harga_sebelumnya is None:
        return
    selisih = harga - harga_sebelumnya
    persen = (selisih / harga_sebelumnya) * 100
    if abs(persen) >= threshold:
        arah = "NAIK 🚀" if persen > 0 else "TURUN 🔻"
        print(f"\n⚠️  ALERT! Harga {arah}")
        print(f"   Rp{harga_sebelumnya:,.0f} → Rp{harga:,.0f} ({persen:+.2f}%)\n")

def tampilkan_historis(data):
    print("\n📊 Historis 30 Hari Terakhir:")
    print(f"{'Tanggal':<15} {'Harga (IDR)':>15}")
    print("-" * 32)
    for d in data[-10:]:
        print(f"{d['tanggal']:<15} Rp{d['close']:>12,.2f}")
    with open("bbca_historis.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Tanggal", "Harga Close (IDR)"])
        for d in data:
            writer.writerow([d["tanggal"], d["close"]])
    print("Tersimpan: bbca_historis.csv")

# ── MAIN ──
print("=" * 40)
print("  BBCA Monitor - Yahoo Finance")
print("  PT Bank Central Asia Tbk (IDX)")
print("=" * 40)

print("\n⏳ Mengambil data historis...")
historis = scrape_historis()
if historis:
    tampilkan_historis(historis)
else:
    print("Gagal ambil data historis.")

INTERVAL = 60
THRESHOLD = 2.0
harga_sebelumnya = None

print(f"\n🔄 Monitoring aktif sesuai jam pasar IDX...")
print("Tekan CTRL+C untuk berhenti\n")

while True:
    try:
        buka, status = jam_pasar()
        waktu = datetime.now().strftime("%H:%M:%S")

        if buka:
            harga = scrape_harga()
            if harga:
                cek_notifikasi(harga, harga_sebelumnya, THRESHOLD)
                simpan_csv(harga)
                print(f"[{waktu}] 🟢 {status} | BBCA: Rp{harga:,.0f}", end="")
                if harga_sebelumnya:
                    selisih = harga - harga_sebelumnya
                    print(f"  ({selisih:+.0f})", end="")
                print()
                harga_sebelumnya = harga
            else:
                print(f"[{waktu}] Gagal ambil harga, mencoba lagi...")
            time.sleep(INTERVAL)
        else:
            print(f"[{waktu}] 🔴 Pasar {status}", end="\r")
            time.sleep(30)  # cek tiap 30 detik saat tutup

    except KeyboardInterrupt:
        print("\n\nMonitoring dihentikan.")
        print("Data tersimpan di: bbca_realtime.csv & bbca_historis.csv")
        break
