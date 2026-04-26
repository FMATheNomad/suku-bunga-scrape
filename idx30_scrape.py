import cloudscraper
import csv, time, os
from datetime import datetime

# Daftar 30 saham IDX30
IDX30 = [
    "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK",
    "BMRI.JK", "BRIS.JK", "BRPT.JK", "BUKA.JK", "CPIN.JK",
    "EMTK.JK", "ERAA.JK", "EXCL.JK", "GGRM.JK", "GOTO.JK",
    "HMSP.JK", "ICBP.JK", "INCO.JK", "INDF.JK", "INKP.JK",
    "INTP.JK", "KLBF.JK", "MDKA.JK", "MEDC.JK", "PGAS.JK",
    "PTBA.JK", "SMGR.JK", "TLKM.JK", "UNTR.JK", "UNVR.JK"
]

def jam_pasar():
    now = datetime.now()
    hari = now.weekday()
    if hari >= 5:
        return False, "Tutup (Weekend)"
    waktu = now.hour * 60 + now.minute
    if 9*60 <= waktu <= 11*60+30:
        return True, "Sesi 1"
    elif 13*60+30 <= waktu <= 15*60+49:
        return True, "Sesi 2"
    elif waktu < 9*60:
        return False, "Belum buka (09:00)"
    elif 11*60+30 < waktu < 13*60+30:
        return False, "Jeda siang (13:30)"
    else:
        return False, "Sudah tutup"

def scrape_satu(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        scraper = cloudscraper.create_scraper()
        res = scraper.get(url, headers=headers, timeout=10)
        data = res.json()
        meta = data["chart"]["result"][0]["meta"]
        harga = meta["regularMarketPrice"]
        volume = meta.get("regularMarketVolume", 0)
        prev_close = meta.get("previousClose", 0)
        if harga and prev_close:
            perubahan = harga - prev_close
            persen = (perubahan / prev_close) * 100
        else:
            perubahan = 0
            persen = 0
        return {
            "ticker": ticker.replace(".JK", ""),
            "harga": harga,
            "perubahan": round(perubahan, 2),
            "persen": round(persen, 2),
            "volume": volume
        }
    except:
        return None

def simpan_csv(semua_data, waktu):
    filename = "idx30_realtime.csv"
    file_baru = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if file_baru:
            writer.writerow(["Waktu", "Ticker", "Harga", "Perubahan", "Persen%", "Volume"])
        for d in semua_data:
            writer.writerow([waktu, d["ticker"], d["harga"],
                           d["perubahan"], d["persen"], d["volume"]])

def tampilkan(semua_data, waktu, status):
    os.system("clear")
    print("=" * 60)
    print(f"  IDX30 Monitor | {waktu} | 🟢 {status}")
    print("=" * 60)
    print(f"{'Ticker':<8} {'Harga':>10} {'Perubahan':>12} {'%':>8} {'Volume':>12}")
    print("-" * 60)

    # Urutkan by % perubahan
    semua_data.sort(key=lambda x: x["persen"], reverse=True)

    for d in semua_data:
        emoji = "🟢" if d["persen"] >= 0 else "🔴"
        print(f"{d['ticker']:<8} Rp{d['harga']:>8,.0f} "
              f"{d['perubahan']:>+10.0f} "
              f"{d['persen']:>+7.2f}% "
              f"{emoji} {d['volume']:>10,}")
    print("-" * 60)
    print(f"Naik : {sum(1 for d in semua_data if d['persen'] > 0)} saham")
    print(f"Turun: {sum(1 for d in semua_data if d['persen'] < 0)} saham")
    print(f"Flat : {sum(1 for d in semua_data if d['persen'] == 0)} saham")
    print("\nTersimpan: idx30_realtime.csv | CTRL+C untuk berhenti")

# ── MAIN ──
print("=" * 60)
print("  IDX30 Multi-Stock Monitor")
print("=" * 60)
print("Memulai monitoring 30 saham IDX30...")
print("Tekan CTRL+C untuk berhenti\n")

while True:
    try:
        buka, status = jam_pasar()
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if buka:
            print(f"Mengambil data 30 saham... ({datetime.now().strftime('%H:%M:%S')})")
            semua_data = []
            for i, ticker in enumerate(IDX30):
                hasil = scrape_satu(ticker)
                if hasil:
                    semua_data.append(hasil)
                print(f"  {i+1}/30 {ticker}", end="\r")
                time.sleep(1)  # jeda 1 detik antar request

            if semua_data:
                tampilkan(semua_data, waktu, status)
                simpan_csv(semua_data, waktu)

            # Hitung sisa waktu tunggu
            elapsed = len(IDX30)
            sisa = max(0, 60 - elapsed)
            time.sleep(sisa)

        else:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 🔴 Pasar {status}    ", end="")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\nMonitoring dihentikan.")
        print("Data tersimpan di: idx30_realtime.csv")
        break
