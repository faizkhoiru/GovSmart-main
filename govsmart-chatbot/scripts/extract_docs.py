"""
Fase 2 - Ekstraksi teks knowledge base GovSmart.

Jalankan dari folder govsmart-chatbot (venv aktif):
    python scripts/extract_docs.py                 # semua dokumen
    python scripts/extract_docs.py --only perbup   # hanya file yang namanya memuat "perbup"
    python scripts/extract_docs.py --no-ocr        # tanpa OCR (uji cepat)

Hasil:
    data/clean/<topik>/<nama_file>.jsonl   satu baris JSON per halaman
    data/clean/_laporan.md                 ringkasan kualitas ekstraksi
    data/raw/ocr_cache/<nama_file>/pNNNN.txt   cache OCR (proses bisa dilanjutkan)
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

KB = Path("knowledge_base")
OUT = Path("data/clean")
CACHE = Path("data/raw/ocr_cache")

MIN_CHARS = 150          # halaman dengan teks lebih sedikit dari ini -> coba OCR
OCR_SCALE = 2.5          # kira-kira 180 dpi
NEVER_OCR = ("anri_", "250711_naskah")   # arsip BPUPK: halaman tipis memang tipis
TWO_COLUMN = ("uud1945",)                # PDF dua kolom: baca kolom kiri dulu, lalu kanan

STRUCT = re.compile(
    r"^(BAB\s+[IVXLC]+\b|Pasal\s+\d+|\(\d+\)|[a-z]\.\s|\d+\.\s|BAGIAN\s|Paragraf\s|"
    r"MEMUTUSKAN|Menimbang|Mengingat|Menetapkan|KESATU|KEDUA|KETIGA)"
)


# ---------------------------------------------------------------- SUMBER.md
def baca_sumber():
    """Baca tabel SUMBER.md -> {path relatif: {topik, judul, penerbit, tahun}}."""
    meta = {}
    f = KB / "SUMBER.md"
    if not f.exists():
        return meta
    header = None
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if "File" in cells:
                header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells))
        if row.get("file"):
            meta[row["file"]] = {
                "judul": row.get("judul dokumen", ""),
                "penerbit": row.get("penerbit", ""),
                "tahun": row.get("tahun", ""),
            }
    return meta


# ---------------------------------------------------------------- OCR
_ocr_modul = None


def ocr_halaman(page, cache_file):
    """OCR satu halaman pdfium. Hasil: (teks, rata-rata confidence)."""
    global _ocr_modul
    if cache_file.exists():
        isi = cache_file.read_text(encoding="utf-8")
        conf, _, teks = isi.partition("\n")
        return teks, float(conf)
    if _ocr_modul is None:
        from ocrmac import ocrmac
        _ocr_modul = ocrmac
    img = page.render(scale=OCR_SCALE).to_pil()
    hasil = _ocr_modul.OCR(img, recognition_level="accurate").recognize()
    teks, conf = susun_baris(hasil)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(f"{conf:.3f}\n{teks}", encoding="utf-8")
    return teks, conf


def susun_baris(hasil):
    """Urutkan potongan OCR: atas->bawah, lalu kiri->kanan (memperbaiki urutan baca)."""
    if not hasil:
        return "", 0.0
    items = []
    for t, conf, (x, y, w, h) in hasil:
        items.append({"t": t, "c": conf, "x": x, "yc": y + h / 2, "h": h})
    items.sort(key=lambda d: -d["yc"])     # y Vision dimulai dari bawah
    baris, cur = [], [items[0]]
    for it in items[1:]:
        if abs(it["yc"] - cur[0]["yc"]) <= 0.5 * max(cur[0]["h"], it["h"]):
            cur.append(it)
        else:
            baris.append(cur)
            cur = [it]
    baris.append(cur)
    teks = "\n".join(" ".join(i["t"] for i in sorted(b, key=lambda d: d["x"])) for b in baris)
    conf = sum(i["c"] for i in items) / len(items)
    return teks, conf


# ---------------------------------------------------------------- pembersihan
def hapus_header_footer(pages):
    """Hapus baris pendek yang berulang di >=35% halaman (nomor halaman, kop berulang)."""
    n = len(pages)
    if n < 8:
        return pages
    norm = lambda s: re.sub(r"\d+", "#", s.strip().lower())
    # Baris struktur hukum ("Pasal 4", "(1)", "BAB II") JANGAN dianggap header/footer.
    kandidat = lambda l: l.strip() and not STRUCT.match(l.strip())
    hitung = Counter()
    for p in pages:
        for ln in set(norm(l) for l in p.splitlines() if kandidat(l)):
            hitung[ln] += 1
    buang = {ln for ln, c in hitung.items() if c >= 0.35 * n and len(ln) < 100}
    return ["\n".join(l for l in p.splitlines() if not (kandidat(l) and norm(l) in buang)) for p in pages]


def bersihkan(teks):
    teks = re.sub(r"\(cid:\d+\)", "", teks)              # penanda catatan kaki yang rusak
    teks = teks.replace("\u00ad", "").replace("\u00a0", " ")
    teks = re.sub(r"[ \t]+", " ", teks)
    baris = [l.strip() for l in teks.splitlines()]
    baris = [l for l in baris if l and not re.fullmatch(r"[-–]?\s*\d{1,3}\s*[-–]?", l)]
    paragraf = []
    for l in baris:
        if not paragraf or STRUCT.match(l):
            paragraf.append(l)
        elif re.search(r"[A-Za-z]-$", paragraf[-1]) and l[:1].islower():
            paragraf[-1] = paragraf[-1][:-1] + l          # sambung kata terpotong
        else:
            paragraf[-1] += " " + l
    teks = "\n".join(paragraf)
    teks = re.sub(r"(?<=[a-z])- (?=[a-z])", "", teks)      # "member- hentikan"
    return teks.strip()


# ---------------------------------------------------------------- ekstraksi
def proses_pdf(path, ocr_aktif):
    import pdfplumber
    import pypdfium2 as pdfium

    rel = path.relative_to(KB).as_posix()
    boleh_ocr = ocr_aktif and not any(k in rel.lower() for k in NEVER_OCR)
    mentah, metode, confs = [], [], []
    pdf = pdfium.PdfDocument(str(path))
    with pdfplumber.open(str(path)) as plumber:
        total = len(plumber.pages)
        for i in range(total):
            try:
                pg = plumber.pages[i]
                if any(k in rel.lower() for k in TWO_COLUMN):
                    w, h = pg.width, pg.height
                    kiri = pg.crop((0, 0, w / 2, h)).extract_text() or ""
                    kanan = pg.crop((w / 2, 0, w, h)).extract_text() or ""
                    teks = kiri + "\n" + kanan
                else:
                    teks = pg.extract_text() or ""
            except Exception:
                teks = ""
            m, conf = "teks", None
            if boleh_ocr and len(teks.strip()) < MIN_CHARS:
                cache = CACHE / path.stem / f"p{i + 1:04d}.txt"
                sudah = cache.exists()
                ocr_teks, conf = ocr_halaman(pdf[i], cache)
                if len(ocr_teks.strip()) > len(teks.strip()):
                    teks, m = ocr_teks, "ocr"
                if not sudah:
                    print(f"   OCR {rel} hal {i + 1}/{total}", flush=True)
            mentah.append(teks)
            metode.append(m)
            confs.append(conf)
    bersih = [bersihkan(t) for t in hapus_header_footer(mentah)]
    return [
        {"halaman": i + 1, "metode": metode[i], "ocr_conf": confs[i], "teks": bersih[i]}
        for i in range(len(bersih))
    ]


def proses_md(path):
    return [{"halaman": 1, "metode": "md", "ocr_conf": None,
             "teks": path.read_text(encoding="utf-8").strip()}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="hanya file yang path-nya memuat teks ini")
    ap.add_argument("--no-ocr", action="store_true")
    args = ap.parse_args()

    if not KB.exists():
        sys.exit("Jalankan dari folder govsmart-chatbot (knowledge_base/ tidak ditemukan).")
    meta = baca_sumber()
    OUT.mkdir(parents=True, exist_ok=True)
    file_laporan = OUT / "_laporan.md"
    baris_laporan = {}
    if file_laporan.exists():
        for ln in file_laporan.read_text(encoding="utf-8").splitlines():
            if ln.startswith("| ") and not ln.startswith("| File") and not ln.startswith("|---"):
                baris_laporan[ln.split("|")[1].strip()] = ln

    berkas = sorted(p for p in KB.rglob("*") if p.suffix.lower() in (".pdf", ".md")
                    and p.name != "SUMBER.md")
    for path in berkas:
        rel = path.relative_to(KB).as_posix()
        if args.only and args.only.lower() not in rel.lower():
            continue
        topik = path.parent.name
        info = meta.get(rel, {})
        print(f"\n[{topik}] {rel}", flush=True)
        halaman = proses_pdf(path, not args.no_ocr) if path.suffix.lower() == ".pdf" else proses_md(path)

        tujuan = OUT / topik / (path.stem + ".jsonl")
        tujuan.parent.mkdir(parents=True, exist_ok=True)
        with tujuan.open("w", encoding="utf-8") as f:
            for h in halaman:
                rec = {"topik": topik, "file": rel,
                       "judul": info.get("judul") or path.stem,
                       "penerbit": info.get("penerbit", ""), "tahun": info.get("tahun", ""), **h}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        n_ocr = sum(h["metode"] == "ocr" for h in halaman)
        kosong = sum(len(h["teks"]) < 30 for h in halaman)
        confs = [h["ocr_conf"] for h in halaman if h["metode"] == "ocr" and h["ocr_conf"] is not None]
        rata = f"{sum(confs) / len(confs):.2f}" if confs else "-"
        total = sum(len(h["teks"]) for h in halaman)
        baris_laporan[rel] = f"| {rel} | {len(halaman)} | {len(halaman) - n_ocr} | {n_ocr} | {kosong} | {rata} | {total} |"
        print(f"   -> {tujuan}  ({len(halaman)} hal, OCR {n_ocr}, kosong {kosong}, {total} karakter)")

    laporan = ["# Laporan ekstraksi\n",
               "| File | Halaman | Via teks | Via OCR | Kosong | Rata2 conf OCR | Total karakter |",
               "|---|---|---|---|---|---|---|"] + [baris_laporan[k] for k in sorted(baris_laporan)]
    file_laporan.write_text("\n".join(laporan) + "\n", encoding="utf-8")
    print("\nSelesai. Ringkasan: data/clean/_laporan.md")


if __name__ == "__main__":
    main()
