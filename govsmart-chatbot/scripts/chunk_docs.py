#!/usr/bin/env python3
"""Fase 3 - Chunking dokumen GovSmart (RAG).

Letakkan di scripts/chunk_docs.py, lalu jalankan dari root proyek:
    python scripts/chunk_docs.py
    python scripts/chunk_docs.py --sample 2        # tampilkan 2 contoh chunk per dokumen

Input : data/clean/<topik>/<dokumen>.jsonl   (hasil extract_docs.py)
Output: data/chunks/chunks.jsonl             (satu chunk per baris)
        data/chunks/_laporan_chunk.md        (ringkasan + halaman yang dilewati)

Strategi:
  - Dokumen peraturan (Pasal/BAB)  -> dipecah per Pasal, Pasal kecil digabung sampai ~target
  - Markdown (FAQ/panduan)         -> dipecah per heading, heading kecil digabung ke berikutnya
  - Lainnya (naskah, tabel OCR)    -> dipecah per paragraf lalu per kalimat dengan overlap
Setiap chunk membawa metadata: dokumen, topik/koleksi, konteks (BAB/Pasal/heading), rentang halaman.
"""
import argparse
import bisect
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / "data" / "clean"
OUT_DIR = ROOT / "data" / "chunks"

# folder sumber -> koleksi retrieval (3 topik chatbot)
KOLEKSI = {
    "app": "aplikasi",
    "pelaporan": "aplikasi",
    "pemerintah": "pemerintah",
    "nasionalisme": "kenegaraan",
}

# nama file (tanpa ekstensi) -> (judul, jenis). Sesuaikan judulnya bila perlu.
DOC_META = {
    "faq_aplikasi": ("FAQ Aplikasi GovSmart", "faq"),
    "panduan_pelaporan": ("Panduan Pelaporan GovSmart", "panduan"),
    "panduan_nib_oss": ("Panduan NIB dan OSS", "panduan"),
    "perbup_lamongan_40_2025_sop_perizinan": (
        "Perbup Lamongan No. 40 Tahun 2025 tentang SOP Pelayanan Perizinan", "peraturan"),
    "sk_dpmptsp_lamongan_standar_pelayanan_2026": (
        "SK DPMPTSP Lamongan tentang Standar Pelayanan 2026", "peraturan"),
    "uu_24_2009_bendera_bahasa_lambang": (
        "UU No. 24 Tahun 2009 tentang Bendera, Bahasa, dan Lambang Negara serta Lagu Kebangsaan",
        "peraturan"),
    "uud1945_perubahan4": ("UUD 1945 (Perubahan Keempat)", "peraturan"),
    "anri_naskah_sumber_bpupk_1945": ("Naskah Sumber Sidang BPUPK 1945 (ANRI)", "naskah_sejarah"),
}

# halaman yang sengaja dibuang (mis. partitur lagu Indonesia Raya hasil OCR berantakan)
EXCLUDE_PAGES = {
    "uu_24_2009_bendera_bahasa_lambang": set(range(53, 57)),
}

HEAD_RE = re.compile(r"(?m)^(#{1,4})\s+(.+)$")
LEGAL_RE = re.compile(r"(?m)^(?:BAB\s+[IVXLC]+\b|Pasal\s+(?:\d+[A-Z]?|[Il])\b|LAMPIRAN\b)")
# Standar pelayanan: "... Biaya/Tarif ... Produk Pelayanan <NAMA> Sarana dan Prasarana ..."
PRODUK_RE = re.compile(r"Produk\s+(?:Pelayanan\s+)?(.{5,160}?)\s+(?:\d\s+)?Sarana\s+dan", re.S)
MIN_KEEP = 40  # chunk lebih pendek dari ini dibuang (noise)


# ---------------------------------------------------------------- pembersihan
def clean_page(t):
    t = unicodedata.normalize("NFKC", t or "")
    t = t.replace("\r", "").replace("\x0c", "\n")
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # sambung kata yang terpotong di akhir baris
    raw = t.split("\n")
    lines = []
    for i, ln in enumerate(raw):
        s = ln.strip()
        # buang nomor halaman, hanya di 2 baris pertama/terakhir halaman (aman untuk tabel)
        if (i < 2 or i >= len(raw) - 2) and re.fullmatch(
                r"(?:-\s*)?(?:hal(?:aman)?\.?\s*)?\d{1,3}(?:\s*-)?", s, re.I):
            continue
        lines.append(re.sub(r"[ \t]+", " ", s))
    t = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


# ---------------------------------------------------------------- segmentasi
def is_real_heading(text, pos):
    """Hindari salah deteksi 'Pasal 7' yang kebetulan berada di awal baris kutipan."""
    before = text[:pos].rstrip(" \n")
    if not before:
        return True
    prev_line = before.rsplit("\n", 1)[-1].strip()
    return (before[-1] in ".;:)" or prev_line.isupper()
            or re.match(r"(BAB|Bagian)\b", prev_line) is not None)


def find_points(full, mode):
    """-> list (offset_awal, label)"""
    pts = []
    if mode == "md":
        path = []
        for m in HEAD_RE.finditer(full):
            lvl, title = len(m.group(1)), m.group(2).strip()
            path = path[:lvl - 1] + [title]
            pts.append((m.start(), " > ".join(path)))
    elif mode == "legal":
        bab = ""
        for m in LEGAL_RE.finditer(full):
            tok = re.sub(r"^(Pasal)\s+[Il]\b", r"\1 1", m.group(0).strip())  # OCR: "Pasal I" = Pasal 1
            if tok != "LAMPIRAN" and not is_real_heading(full, m.start()):
                continue
            if tok == "LAMPIRAN" or tok.upper().startswith("BAB"):
                line_end = full.find("\n", m.start())
                baris = full[m.start(): line_end if line_end > 0 else None].strip()
                # OCR kadang menyatukan judul BAB dan "Pasal 1" dalam satu baris -> pisahkan labelnya
                pm = re.search(r"\s+Pasal\s+(\d+[A-Z]?|[Il])\b", baris)
                bab = re.split(r"\s+Pasal\b", baris)[0][:80]
                label = f"{bab} > Pasal {'1' if pm.group(1) in ('I', 'l') else pm.group(1)}" if pm else bab
                pts.append((m.start(), label))
            else:
                pts.append((m.start(), f"{bab} > {tok}" if bab else tok))
    else:  # plain: batas paragraf
        for m in re.finditer(r"\n{2,}", full):
            pts.append((m.end(), ""))
    return pts


def build_sections(pts, n):
    if not pts or pts[0][0] > 0:
        pts = [(0, "")] + pts
    secs = []
    for i, (p, lab) in enumerate(pts):
        e = pts[i + 1][0] if i + 1 < len(pts) else n
        if e > p:
            secs.append((p, e, lab))
    return secs


def pack(secs, mode, target, max_chars, min_chars):
    out, cur = [], None  # cur = [start, end, first_label, last_label]
    for s, e, lab in secs:
        if cur is None:
            cur = [s, e, lab, lab]
            continue
        cur_len, sec_len = cur[1] - cur[0], e - s
        if mode == "md":
            can = cur_len < min_chars and cur_len + sec_len <= max_chars
        else:
            can = cur_len + sec_len <= target
        if can:
            if "Pasal" not in cur[2] and "Pasal" in lab:
                cur[2] = lab
            cur[1], cur[3] = e, lab
        else:
            out.append(tuple(cur))
            cur = [s, e, lab, lab]
    if cur:
        out.append(tuple(cur))
    return out


def fmt_label(first, last):
    if first == last or not last:
        return first
    if "Pasal" in first and "Pasal" in last:
        return f"{first} s.d. {last.split(' > ')[-1]}"
    return first


def split_long(text, target, max_chars, overlap):
    """Pecah teks panjang per kalimat, dengan overlap."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?;:])\s+|\n{2,}", text) if s.strip()]
    flat = []
    for s in sents:
        limit = max_chars - overlap  # sisakan ruang untuk overlap agar chunk tidak melebihi max
        while len(s) > limit:  # kalimat super panjang (umum di hasil OCR) -> potong per kata
            cut = s.rfind(" ", 0, limit)
            cut = cut if cut > limit * 0.5 else limit
            flat.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            flat.append(s)
    chunks, cur, cur_len, fresh = [], [], 0, 0
    for s in flat:
        if fresh > 0 and cur_len + len(s) + 1 > target:
            chunks.append(" ".join(cur))
            tail, tl = [], 0
            for t in reversed(cur):
                if tl + len(t) > overlap:
                    break
                tail.insert(0, t)
                tl += len(t) + 1
            cur, cur_len, fresh = tail, tl, 0
        cur.append(s)
        cur_len += len(s) + 1
        fresh += 1
    if fresh > 0:
        chunks.append(" ".join(cur))
    return chunks


# ---------------------------------------------------------------- proses dokumen
def process_doc(path, topik, args, seen):
    stem = path.stem
    judul, jenis = DOC_META.get(stem, (stem.replace("_", " ").title(), "dokumen"))
    koleksi = KOLEKSI.get(topik, topik)
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(ln) for ln in f if ln.strip()]

    kept, skipped = [], []
    excl = EXCLUDE_PAGES.get(stem, set())
    for r in rows:
        h, metode, conf = r.get("halaman", 0), r.get("metode", ""), r.get("ocr_conf")
        if h in excl:
            skipped.append((h, "dikecualikan manual"))
            continue
        if metode == "ocr" and conf is not None and conf < args.min_conf:
            skipped.append((h, f"OCR conf {conf:.2f} < {args.min_conf}"))
            continue
        t = clean_page(r.get("teks", ""))
        if len(t) < 30:
            skipped.append((h, "kosong / terlalu pendek"))
            continue
        kept.append((h, t, metode == "ocr"))

    stats = {"doc": stem, "topik": topik, "judul": judul, "hal_total": len(rows),
             "hal_dipakai": len(kept), "skipped": skipped, "chunks": 0, "lens": []}
    if not kept:
        return [], stats

    starts, pages, ocr_pages, parts, pos = [], [], set(), [], 0
    for h, t, is_ocr in kept:
        starts.append(pos)
        pages.append(h)
        parts.append(t)
        pos += len(t) + 1
        if is_ocr:
            ocr_pages.add(h)
    full = "\n".join(parts)

    def page_at(off):
        return pages[max(0, bisect.bisect_right(starts, off) - 1)]

    if len(HEAD_RE.findall(full)) >= 2:
        mode = "md"
    elif jenis == "peraturan" and len(LEGAL_RE.findall(full)) >= 3:
        mode = "legal"
    else:
        mode = "plain"
    stats["mode"] = mode

    raw_secs = build_sections(find_points(full, mode), len(full))
    if mode == "legal":  # satu 'Pasal' sepanjang >20000 karakter hampir pasti lampiran/uraian, bukan pasal
        raw_secs = [(s, e, f"Lampiran/uraian (lanjutan {l.split(' > ')[-1]})"
                     if (e - s) > 20000 and "Pasal" in l else l) for s, e, l in raw_secs]
    secs = pack(raw_secs, mode, args.target, args.max, args.min)
    chunks, n = [], 0
    for s, e, first, last in secs:
        raw = full[s:e]
        seg = raw.strip()
        if not seg:
            continue
        s += len(raw) - len(raw.lstrip())
        label = fmt_label(first, last)
        if len(seg) <= args.max:
            pieces = [(seg, s)]
        else:
            pieces, cursor = [], 0
            for sub in split_long(seg, args.target, args.max, args.overlap):
                p = seg.find(sub[:50], cursor)
                p = cursor if p < 0 else p
                cursor = p + 1
                pieces.append((sub, s + p))
        for text, off in pieces:
            if len(text) < MIN_KEEP:
                continue
            key = hashlib.sha1(re.sub(r"\s+", " ", text.lower()).encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            ha, hb = page_at(off), page_at(min(off + len(text) - 1, e - 1))
            n += 1
            pm = PRODUK_RE.search(text)
            produk = re.sub(r"\s*(?:Pelayanan)?\s*\d*$", "", pm.group(1)).strip() if pm else ""
            head = judul + (f" | {label}" if label else "") + (f" | Layanan: {produk}" if produk else "")
            chunks.append({
                "id": f"{stem}-{n:04d}",
                "doc_id": stem, "judul": judul, "jenis": jenis,
                "topik": topik, "koleksi": koleksi,
                "konteks": label, "produk": produk,
                "halaman_mulai": ha, "halaman_selesai": hb,
                "sumber_ocr": any(ha <= p <= hb for p in ocr_pages),
                "n_char": len(text),
                "teks": text,
                "teks_embed": f"{head}\n{text}",
            })
            stats["lens"].append(len(text))
    stats["chunks"] = n
    return chunks, stats


def write_report(all_stats, args, path):
    L = ["# Laporan Chunking", "",
         f"Parameter: target={args.target}, max={args.max}, overlap={args.overlap}, "
         f"min={args.min}, min_conf={args.min_conf}", "",
         "| Dokumen | Topik | Mode | Hal dipakai | Chunk | Rata2 | Min | Maks |",
         "|---|---|---|---|---|---|---|---|"]
    for s in all_stats:
        ls = s["lens"] or [0]
        L.append(f"| {s['doc']} | {s['topik']} | {s.get('mode', '-')} | "
                 f"{s['hal_dipakai']}/{s['hal_total']} | {s['chunks']} | "
                 f"{sum(ls) // len(ls)} | {min(ls)} | {max(ls)} |")
    L += ["", "## Halaman yang dilewati", ""]
    for s in all_stats:
        if s["skipped"]:
            L.append(f"**{s['doc']}** ({len(s['skipped'])} hal)")
            by = defaultdict(list)
            for h, why in s["skipped"]:
                by[why].append(h)
            for why, hs in by.items():
                L.append(f"- {why}: hal {', '.join(map(str, hs))}")
            L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=900, help="ukuran chunk ideal (karakter)")
    ap.add_argument("--max", type=int, default=1300, help="ukuran chunk maksimum (karakter)")
    ap.add_argument("--overlap", type=int, default=150, help="overlap antar chunk panjang")
    ap.add_argument("--min", type=int, default=120, help="heading markdown lebih kecil dari ini digabung")
    ap.add_argument("--min-conf", type=float, default=0.3, help="halaman OCR di bawah ini dibuang")
    ap.add_argument("--sample", type=int, default=0, help="tampilkan N contoh chunk per dokumen")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in IN_DIR.glob("*/*.jsonl") if not p.name.startswith("_"))
    if not files:
        raise SystemExit(f"Tidak ada .jsonl di {IN_DIR}. Jalankan extract_docs.py dulu.")

    seen, all_chunks, all_stats = set(), [], []
    for p in files:
        chunks, st = process_doc(p, p.parent.name, args, seen)
        all_chunks += chunks
        all_stats.append(st)
        ls = st["lens"] or [0]
        print(f"[{st['topik']}] {st['doc']}: {st['hal_dipakai']}/{st['hal_total']} hal "
              f"-> {st['chunks']} chunk (rata2 {sum(ls) // len(ls)} char, mode {st.get('mode', '-')})")
        for i in range(args.sample and min(args.sample, len(chunks))):
            c = chunks[i * len(chunks) // args.sample]
            print(f"   --- {c['id']} | {c['konteks']} | hal {c['halaman_mulai']}-{c['halaman_selesai']}")
            print("   " + c["teks"][:300].replace("\n", " "))

    with open(OUT_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    write_report(all_stats, args, OUT_DIR / "_laporan_chunk.md")
    print(f"\nSelesai: {len(all_chunks)} chunk -> {OUT_DIR / 'chunks.jsonl'}")
    print(f"Laporan: {OUT_DIR / '_laporan_chunk.md'}")


if __name__ == "__main__":
    main()
