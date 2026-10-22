#!/usr/bin/env python3
"""Tahap 4b - Retriever hybrid untuk chatbot GovSmart.

Pencarian = embedding (makna) + BM25 (kata kunci persis, mis. "Pasal 57", "KKPR", "NIB"),
digabung dengan Reciprocal Rank Fusion. Bisa difilter per koleksi (aplikasi / pemerintah / kenegaraan)
sesuai hasil intent router nanti.

Pemakaian (dari root proyek):
    python scripts/retriever.py "berapa lama registrasi KKPR" --koleksi pemerintah -k 5
    python scripts/retriever.py --eval          # uji kualitas retrieval dengan pertanyaan acuan

Pemakaian di kode (mis. di FastAPI):
    from scripts.retriever import Retriever
    r = Retriever()
    hasil = r.search("apa bentuk bendera negara?", k=4, koleksi="kenegaraan")
"""
import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "chunks" / "chunks.jsonl"
INDEX_DIR = ROOT / "data" / "index"

# Naskah sejarah (transkrip sidang) jumlahnya sangat banyak dan berbahasa kuno -> diberi bobot lebih rendah
JENIS_BOBOT = {"naskah_sejarah": 0.6}
# Lampiran peraturan hasil OCR berisi bagan alir yang terbaca berantakan; isinya biasa ada juga di dokumen yang lebih bersih
LAMPIRAN_OCR_BOBOT = 0.7
# Chunk standar pelayanan punya nama layanan (field 'produk'). Makin besar porsi nama layanan yang tercakup
# pertanyaan, makin tinggi skornya (membedakan 'Registrasi KKPR' dari 'Penerbitan Persetujuan KKPR').
PRODUK_BOOST = 0.4

STOP = set("yang dan di ke dari untuk dengan pada adalah itu ini apa berapa bagaimana saja atau dalam "
           "akan oleh ada saya bisa dapat apakah siapa kapan mengapa kenapa".split())


def tokenize(text):
    return [t for t in re.findall(r"\w+", text.lower()) if t not in STOP]


# Singkatan -> kepanjangan. Dokumen sering memakai nama lengkap, sedangkan pengguna menulis singkatan
# (mis. "KKPR"). Kepanjangan ditambahkan ke query saat pencarian. Tambah sesuai kebutuhan.
ALIAS = {
    "kkpr": "Kesesuaian Kegiatan Pemanfaatan Ruang",
    "pbg": "Persetujuan Bangunan Gedung",
    "slf": "Sertifikat Laik Fungsi",
    "nib": "Nomor Induk Berusaha",
    "oss": "Online Single Submission perizinan berusaha terintegrasi elektronik",
    "umkm": "Usaha Mikro Kecil dan Menengah",
    "umku": "Perizinan Berusaha untuk Menunjang Kegiatan Usaha",
    "amdal": "Analisis Mengenai Dampak Lingkungan",
    "sppl": "Surat Pernyataan Pengelolaan Lingkungan",
    "pkplh": "Pernyataan Kesanggupan Pengelolaan dan Pemantauan Lingkungan Hidup",
    "skkl": "Surat Keputusan Kelayakan Lingkungan Hidup",
    "dpmptsp": "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu",
    "opd": "Organisasi Perangkat Daerah",
    "rtr": "Rencana Tata Ruang",
    "bpupk": "Badan Penyelidik Usaha-usaha Persiapan Kemerdekaan Indonesia",
    "uud": "Undang-Undang Dasar Negara Republik Indonesia",
    "nkri": "Negara Kesatuan Republik Indonesia",
}


try:
    from .typo_corrector import koreksi_teks
except ImportError:
    try:
        from typo_corrector import koreksi_teks
    except ImportError:
        def koreksi_teks(t): return t


def expand_query(q):
    q_norm = koreksi_teks(q)
    # Cari alias baik dari kata asli maupun kata yang sudah dikoreksi
    tokens = dict.fromkeys(re.findall(r"\w+", (q + " " + q_norm).lower()))
    extra = [ALIAS[t] for t in tokens if t in ALIAS]
    return q_norm + (" (" + "; ".join(extra) + ")" if extra else "")


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.n = len(docs)
        self.tf = [Counter(d) for d in docs]
        self.dl = [len(d) for d in docs]
        self.avgdl = sum(self.dl) / max(self.n, 1)
        df = Counter()
        for d in docs:
            df.update(set(d))
        self.idf = {t: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, q_tokens):
        s = np.zeros(self.n, dtype="float32")
        for t in set(q_tokens):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i, tf in enumerate(self.tf):
                f = tf.get(t)
                if f:
                    s[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
        return s


class Retriever:
    def __init__(self):
        raw = CHUNKS.read_bytes()
        self.chunks = [json.loads(ln) for ln in raw.decode("utf-8").splitlines() if ln.strip()]
        meta = json.loads((INDEX_DIR / "index_meta.json").read_text(encoding="utf-8"))
        if meta["chunks_sha1"] != hashlib.sha1(raw).hexdigest():
            raise RuntimeError("chunks.jsonl berubah sejak indeks dibuat. Jalankan build_index.py ulang.")
        self.model_name = meta["model"]
        self.emb = np.load(INDEX_DIR / "embeddings.npy")
        self.bm25 = BM25([tokenize(c["teks_embed"]) for c in self.chunks])
        self.koleksi = np.array([c["koleksi"] for c in self.chunks])
        self.produk_tok = [set(tokenize(c["produk"])) if c.get("produk") else set() for c in self.chunks]
        self.bobot = np.array([self._bobot(c) for c in self.chunks], dtype="float32")
        self._model = None

    @staticmethod
    def _bobot(c):
        w = JENIS_BOBOT.get(c["jenis"], 1.0)
        if c.get("sumber_ocr") and c.get("konteks", "").startswith("LAMPIRAN"):
            w *= LAMPIRAN_OCR_BOBOT
        return w

    def _encode_query(self, q):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device="cpu")
            self._model.max_seq_length = 512
        return self._model.encode(["query: " + q], normalize_embeddings=True)[0].astype("float32")

    def search(self, query, k=5, koleksi=None, pool=40, tetangga=0):
        """-> list dict: chunk, skor (RRF x bobot), dense (cosine).

        tetangga=1: setiap hasil diikuti chunk berikutnya di dokumen yang sama (bertanda "tetangga": True),
        berguna bila jawaban terpotong di batas chunk (mis. langkah prosedur di satu chunk, jangka waktu di chunk berikutnya).
        """
        query = expand_query(query)
        if koleksi is None:
            mask = np.ones(len(self.chunks), dtype=bool)
        else:
            mask = np.isin(self.koleksi, [koleksi] if isinstance(koleksi, str) else list(koleksi))
        dense = self.emb @ self._encode_query(query)
        bm = self.bm25.scores(tokenize(query))
        dense_m = np.where(mask, dense, -np.inf)
        bm_m = np.where(mask, bm, -np.inf)

        fused = defaultdict(float)
        for r, i in enumerate(np.argsort(-dense_m)[:pool]):
            if np.isfinite(dense_m[i]):
                fused[int(i)] += 1.0 / (60 + r + 1)
        for r, i in enumerate(np.argsort(-bm_m)[:pool]):
            if np.isfinite(bm_m[i]) and bm_m[i] > 0:
                fused[int(i)] += 1.0 / (60 + r + 1)
        qt = set(tokenize(query))
        for i in fused:
            fused[i] *= float(self.bobot[i])
            pt = self.produk_tok[i]
            if pt:
                fused[i] *= 1 + PRODUK_BOOST * len(qt & pt) / len(pt)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        out = [{"chunk": self.chunks[i], "skor": fused[i], "dense": float(dense[i])} for i in top]
        if tetangga:
            seen = set(top)
            for i in top:
                for j in range(i + 1, min(i + 1 + tetangga, len(self.chunks))):
                    if self.chunks[j]["doc_id"] != self.chunks[i]["doc_id"]:
                        break
                    if j not in seen:
                        seen.add(j)
                        out.append({"chunk": self.chunks[j], "skor": 0.0, "dense": float(dense[j]), "tetangga": True})
        return out


# Set uji awal. Sesuaikan/tambah dengan isi dokumenmu sendiri (terutama FAQ dan panduan aplikasi).
# koleksi = koleksi yang akan dipilih router; docs = dokumen yang benar; kata = potongan teks yang harus ada.
EVAL = [
    {"q": "Berapa lama proses registrasi KKPR?", "koleksi": "pemerintah",
     "docs": ["sk_dpmptsp_lamongan_standar_pelayanan_2026", "perbup_lamongan_40_2025_sop_perizinan"], "kata": "5 Hari"},
    {"q": "Apakah ada biaya untuk Registrasi Kesesuaian Kegiatan Pemanfaatan Ruang?", "koleksi": "pemerintah",
     "docs": ["sk_dpmptsp_lamongan_standar_pelayanan_2026", "perbup_lamongan_40_2025_sop_perizinan"], "kata": "Tidak ada biaya"},
    {"q": "Berapa hari izin praktek tenaga kesehatan hewan diproses?", "koleksi": "pemerintah",
     "docs": ["sk_dpmptsp_lamongan_standar_pelayanan_2026", "perbup_lamongan_40_2025_sop_perizinan"], "kata": "14 Hari"},
    {"q": "Bagaimana cara menghitung retribusi PBG?", "koleksi": "pemerintah",
     "docs": ["sk_dpmptsp_lamongan_standar_pelayanan_2026", "perbup_lamongan_40_2025_sop_perizinan"], "kata": "Luas Total Lantai"},
    {"q": "Apa bentuk negara Indonesia menurut UUD 1945?", "koleksi": "kenegaraan",
     "docs": ["uud1945_perubahan4"], "kata": "negara kesatuan"},
    {"q": "Bagaimana ketentuan bendera negara Sang Merah Putih?", "koleksi": "kenegaraan",
     "docs": ["uu_24_2009_bendera_bahasa_lambang"], "kata": "Merah Putih"},
    {"q": "Apa bahasa negara Indonesia?", "koleksi": "kenegaraan",
     "docs": ["uu_24_2009_bendera_bahasa_lambang", "uud1945_perubahan4"], "kata": "Bahasa Indonesia"},
    {"q": "Berapa digit NIK saat registrasi akun?", "koleksi": "aplikasi",
     "docs": ["faq_aplikasi", "panduan_pelaporan"], "kata": "16"},
    {"q": "Berapa karakter minimal isi laporan pengaduan?", "koleksi": "aplikasi",
     "docs": ["faq_aplikasi", "panduan_pelaporan"], "kata": "20"},
]


def run_eval(r, k=5):
    hits, via_t = Counter(), 0

    def cocok(h, e):
        c = h["chunk"]
        return c["doc_id"] in e["docs"] and (not e.get("kata") or e["kata"].lower() in c["teks"].lower())

    for e in EVAL:
        res = r.search(e["q"], k=k, koleksi=e["koleksi"], tetangga=1)
        prim = [h for h in res if not h.get("tetangga")]
        rank = next((i for i, h in enumerate(prim, 1) if cocok(h, e)), None)
        for n in (1, 3, 5):
            if rank and rank <= n:
                hits[n] += 1
        lewat_tetangga = rank is None and any(cocok(h, e) for h in res if h.get("tetangga"))
        via_t += lewat_tetangga
        status = f"OK@{rank}" if rank else ("OK via tetangga" if lewat_tetangga else "MISS")
        print(f"[{status}] {e['q']}")
        if not rank:
            for h in prim[:3]:
                c = h["chunk"]
                print(f"      - {c['doc_id']} | {c['konteks']} | hal {c['halaman_mulai']} | {c['teks'][:80]!r}")
    n = len(EVAL)
    print(f"\nhit@1 {hits[1]}/{n} | hit@3 {hits[3]}/{n} | hit@5 {hits[5]}/{n} "
          f"| tambahan lewat chunk tetangga: {via_t} -> total terjawab {hits[5] + via_t}/{n}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--koleksi", choices=["aplikasi", "pemerintah", "kenegaraan"])
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--tetangga", type=int, default=0, help="sertakan N chunk berikutnya dari tiap hasil")
    ap.add_argument("--eval", action="store_true")
    args = ap.parse_args()

    r = Retriever()
    if args.eval:
        return run_eval(r, args.k)
    if not args.query:
        raise SystemExit('Beri pertanyaan, contoh: python scripts/retriever.py "apa itu NIB?" --koleksi pemerintah')
    for i, h in enumerate(r.search(args.query, k=args.k, koleksi=args.koleksi, tetangga=args.tetangga), 1):
        c = h["chunk"]
        tag = " [tetangga]" if h.get("tetangga") else ""
        print(f"\n#{i} skor {h['skor']:.4f} (cos {h['dense']:.3f}) | {c['koleksi']} | {c['doc_id']}{tag}")
        print(f"   {c['konteks']} | hal {c['halaman_mulai']}-{c['halaman_selesai']}"
              + (f" | layanan: {c['produk']}" if c.get("produk") else ""))
        print("   " + c["teks"][:350].replace("\n", " "))


if __name__ == "__main__":
    main()
