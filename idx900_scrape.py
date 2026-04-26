import cloudscraper
import json, csv, time, os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

TICKERS_IDX = [
    "AALI","ABBA","ABDA","ABMM","ACES","ACST","ADHI","ADMF","ADRO","AGRO",
    "AKRA","AKSI","ALDO","ALMI","AMRT","ANTM","APLN","ARNA","ASII","ASRM",
    "ASSA","AUTO","BABP","BAJA","BBCA","BBNI","BBRI","BBTN","BDMN","BFIN",
    "BGGT","BHIT","BIPI","BISI","BJBR","BJTM","BKSL","BMRI","BMTR","BNGA",
    "BNII","BOBA","BOLT","BPFI","BRAM","BRIS","BRPT","BSDE","BTPN","BUDI",
    "BUKA","BULL","BUMI","CAKK","CAMP","CARS","CASA","CEKA","CFIN","CINT",
    "CITA","CLEO","CPIN","CSAP","CTRA","DART","DCII","DEWA","DILD","DLTA",
    "DMAS","DNET","DOID","DPNS","DSNG","DSSA","DUTI","DVLA","EAST","EKAD",
    "ELSA","ELTY","EMTK","EPMT","ERAA","ESSA","EXCL","FAST","FASW","FOOD",
    "FREN","GAMA","GDST","GGRM","GIAA","GJTL","GOTO","GPRA","HEAL","HERO",
    "HEXA","HITS","HMSP","HOKI","HRUM","ICBP","INCO","INDF","INDS","INDY",
    "INKP","INTP","ISAT","ISSP","JPFA","JRPT","JSMR","KAEF","KBLI","KBLM",
    "KDSI","KEEN","KEJU","KIAS","KIJA","KLBF","KOIN","KPIG","LCNP","LEAD",
    "LINK","LION","LMSH","LPCK","LPKR","LPPF","LSIP","LTLS","MAPI","MARK",
    "MASA","MBSS","MBTO","MCAS","MDKA","MDLN","MEDC","MEGA","MERK","MFIN",
    "MGRO","MIDI","MIKA","MKPI","MLBI","MNCN","MPPA","MRAT","MREI","MRPH",
    "MSKY","MTEL","MTLA","MYOH","NCKL","NISP","NOBU","NRCA","OMRE","PADI",
    "PALM","PANR","PANS","PBID","PBRX","PGAS","PGEO","PICO","PJAA","PLIN",
    "PNBN","PNBS","PNIN","PNLF","POWR","PPRO","PRAS","PRDA","PTBA","PTPP",
    "PTRO","PWON","PYFA","RDTX","RICY","ROTI","RUIS","SCCO","SCMA","SGRO",
    "SIDO","SILO","SIMP","SIPD","SKBM","SKLT","SMGR","SMRA","SMSM","SOHO",
    "SPTO","SRIL","SRTG","SSIA","SSMS","STAA","STTP","TBIG","TBLA","TCID",
    "TELE","TINS","TKIM","TLKM","TMAS","TOBA","TOWR","TPMA","TRIM","TRST",
    "TSPC","TURI","UNSP","UNTR","UNVR","VOKS","WEGE","WIFI","WIIM","WIKA",
    "WINS","WSBP","WTON","YPAS","BNBA","BGTG","COAL","COCO","LCKM","KOBX",
    "BOCA","ASGR","PGLI","ICON","DFAM","AMIN","BELL","BCAP","SQMI","PRIM",
    "TRUS","INTD","VIVA","MARI","KREN","KUAS","ELTY","PKPK","CASH","WSBP",
    "BFIN","RODA","BNBA"
]

# Hapus duplikat
TICKERS_IDX = list(dict.fromkeys(TICKERS_IDX))

def jam_pasar():
    now = datetime.now()
    if now.weekday() >= 5:
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
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.JK?interval=1d&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        scraper = cloudscraper.create_scraper()
        res = scraper.get(url, headers=headers, timeout=8)
        data = res.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c]
        if len(closes) < 2:
            return None
        harga = closes[-1]
        prev = closes[-2]
        perubahan = harga - prev
        persen = (perubahan / prev) * 100
        return {
            "ticker": ticker,
            "harga": round(harga),
            "perubahan": round(perubahan),
            "persen": round(persen, 2)
        }
    except:
        return None

def scrape_paralel(tickers, max_workers=10):
    naik, turun = [], []
    selesai = 0
    total = len(tickers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_satu, ticker): ticker
                   for ticker in tickers}
        for future in as_completed(futures):
            selesai += 1
            print(f"  ⏳ {selesai}/{total} selesai...", end="\r")
            hasil = future.result()
            if hasil:
                if hasil["persen"] > 0:
                    naik.append(hasil)
                elif hasil["persen"] < 0:
                    turun.append(hasil)

    naik.sort(key=lambda x: x["persen"], reverse=True)
    turun.sort(key=lambda x: x["persen"])
    return naik, turun

def load_sebelumnya(filename="idx_history.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def simpan_history(data, filename="idx_history.json"):
    with open(filename, "w") as f:
        json.dump(data, f)

def cek_perubahan_baru(lama, naik, turun):
    """Hanya tampilkan yang BARU berubah dari update sebelumnya"""
    baru_naik, baru_turun = [], []
    for d in naik:
        ticker = d["ticker"]
        persen_baru = d["persen"]
        persen_lama = lama.get(ticker, 0)
        if abs(persen_baru - persen_lama) >= 0.1:  # ada perubahan signifikan
            baru_naik.append(d)
    for d in turun:
        ticker = d["ticker"]
        persen_baru = d["persen"]
        persen_lama = lama.get(ticker, 0)
        if abs(persen_baru - persen_lama) >= 0.1:
            baru_turun.append(d)
    return baru_naik, baru_turun

def simpan_csv(naik, turun, waktu):
    filename = f"idx_all_{datetime.now().strftime('%Y%m%d')}.csv"
    file_baru = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if file_baru:
            writer.writerow(["Waktu","Ticker","Harga","Perubahan","Persen%","Status"])
        for d in naik:
            writer.writerow([waktu, d["ticker"], d["harga"], d["perubahan"], d["persen"], "NAIK"])
        for d in turun:
            writer.writerow([waktu, d["ticker"], d["harga"], d["perubahan"], d["persen"], "TURUN"])
    return filename

def tampilkan(naik, turun, baru_naik, baru_turun, waktu, status, durasi):
    os.system("clear")
    print("=" * 55)
    print(f"  IDX Monitor | {waktu}")
    print(f"  Status: 🟢 {status} | Proses: {durasi:.0f} detik")
    print(f"  Total: {len(TICKERS_IDX)} saham")
    print("=" * 55)

    # Alert perubahan baru
    if baru_naik or baru_turun:
        print(f"\n🔔 BARU BERUBAH:")
        if baru_naik:
            print(f"  🚀 Naik: {', '.join([d['ticker'] for d in baru_naik[:10]])}")
        if baru_turun:
            print(f"  🔻 Turun: {', '.join([d['ticker'] for d in baru_turun[:10]])}")
    else:
        print(f"\n✅ Tidak ada perubahan signifikan")

    # Top naik
    print(f"\n🚀 TOP NAIK ({len(naik)} saham)")
    print(f"{'Ticker':<8} {'Harga':>10} {'%':>8}")
    print("-" * 30)
    for d in naik[:15]:
        print(f"{d['ticker']:<8} Rp{d['harga']:>8,} {d['persen']:>+7.2f}%")
    if len(naik) > 15:
        print(f"  ... +{len(naik)-15} saham lainnya")

    # Top turun
    print(f"\n🔻 TOP TURUN ({len(turun)} saham)")
    print(f"{'Ticker':<8} {'Harga':>10} {'%':>8}")
    print("-" * 30)
    for d in turun[:15]:
        print(f"{d['ticker']:<8} Rp{d['harga']:>8,} {d['persen']:>+7.2f}%")
    if len(turun) > 15:
        print(f"  ... +{len(turun)-15} saham lainnya")

    print(f"\n{'='*55}")
    print(f"Naik: {len(naik)} | Turun: {len(turun)} | Total: {len(naik)+len(turun)}")
    print(f"Update berikutnya: 60 detik | CTRL+C berhenti")

# ── MAIN ──
print("=" * 55)
print(f"  IDX Monitor - {len(TICKERS_IDX)} Saham")
print(f"  Mode: PARALEL (10 thread)")
print("=" * 55)
print("Tekan CTRL+C untuk berhenti\n")

data_lama = load_sebelumnya()

while True:
    try:
        buka, status = jam_pasar()
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if buka:
            print(f"\n[{waktu}] 🟢 {status} - Mulai scraping paralel...")
            mulai = time.time()

            naik, turun = scrape_paralel(TICKERS_IDX, max_workers=10)

            durasi = time.time() - mulai

            # Cek perubahan dari update sebelumnya
            baru_naik, baru_turun = cek_perubahan_baru(data_lama, naik, turun)

            # Update history
            data_sekarang = {}
            for d in naik + turun:
                data_sekarang[d["ticker"]] = d["persen"]
            simpan_history(data_sekarang)
            data_lama = data_sekarang

            tampilkan(naik, turun, baru_naik, baru_turun, waktu, status, durasi)
            filename = simpan_csv(naik, turun, waktu)
            print(f"📁 Tersimpan: {filename}")

            time.sleep(60)
        else:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 🔴 Pasar {status}    ", end="")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\nMonitoring dihentikan.")
        break
