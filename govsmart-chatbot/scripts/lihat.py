"""Lihat hasil ekstraksi.
  python scripts/lihat.py perbup 12          -> tampilkan halaman 12
  python scripts/lihat.py perbup "jangka waktu"  -> cari kata, tampilkan potongan + nomor halaman
"""
import glob
import json
import sys

kunci, arg = sys.argv[1].lower(), sys.argv[2]
for f in sorted(glob.glob("data/clean/*/*.jsonl")):
    if kunci not in f.lower():
        continue
    rows = [json.loads(l) for l in open(f, encoding="utf-8")]
    if arg.isdigit():
        r = rows[int(arg) - 1]
        print(f"[{f}] hal {r['halaman']} (metode {r['metode']}, conf {r['ocr_conf']})\n")
        print(r["teks"])
    else:
        for r in rows:
            t = r["teks"]
            i = t.lower().find(arg.lower())
            if i >= 0:
                print(f"hal {r['halaman']}: ..." + t[max(0, i - 80): i + 200].replace("\n", " ") + "...")
