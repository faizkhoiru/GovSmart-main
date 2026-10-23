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
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                # Runtime image intentionally omits Torch; BM25 remains usable.
                self._model = False
            else:
                self._model = SentenceTransformer(self.model_name, device="cpu")
                self._model.max_seq_length = 512
        if self._model is False:
            return None
        return self._model.encode(["query: " + q], normalize_embeddings=True)[0].astype("float32")

    def _dense_scores(self, query):
        encoded = self._encode_query(query)
        return self.emb @ encoded if encoded is not None else np.zeros(len(self.chunks), dtype="float32")

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
        dense = self._dense_scores(query)
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

# Variasi uji bahasa normal, santai, singkatan, dan typo ringan.
# Variasi dipakai untuk evaluasi router/retriever, bukan fakta baru.
_VARIANT_SEEDS = [
    ("Berapa lama proses registrasi KKPR?", "pemerintah"),
    ("Apa syarat registrasi KKPR?", "pemerintah"),
    ("Berapa biaya pengurusan izin?", "pemerintah"),
    ("Bagaimana cara mengurus NIB?", "pemerintah"),
    ("Apa syarat membuat PBG?", "pemerintah"),
    ("Bagaimana cara daftar akun GovSmart?", "aplikasi"),
    ("Berapa digit NIK untuk membuat akun?", "aplikasi"),
    ("Bagaimana cara membuat pengaduan?", "aplikasi"),
    ("Bagaimana cara upload foto laporan?", "aplikasi"),
    ("Apa arti Pancasila?", "kenegaraan"),
    ("Apa bahasa negara Indonesia?", "kenegaraan"),
    ("Bagaimana aturan bendera Merah Putih?", "kenegaraan"),
    ("Apa itu Persetujuan Lingkungan?", "pemerintah"),
    ("Bagaimana cara mengurus izin reklame?", "pemerintah"),
    ("Apa syarat izin usaha UMKM?", "pemerintah"),
    ("Bagaimana prosedur pelayanan publik?", "pemerintah"),
    ("Apa itu standar pelayanan?", "pemerintah"),
    ("Bagaimana cara mengurus KTP?", "pemerintah"),
    ("Apa syarat membuat Kartu Keluarga?", "pemerintah"),
    ("Bagaimana cara mengubah data kependudukan?", "pemerintah"),
    ("Apa fungsi DPMPTSP?", "pemerintah"),
    ("Bagaimana cara melapor jalan rusak?", "pemerintah"),
    ("Bagaimana cara melapor sampah menumpuk?", "pemerintah"),
    ("Apa layanan Dinas Kesehatan?", "pemerintah"),
    ("Bagaimana cara menghubungi dinas terkait?", "pemerintah"),
    ("Apa saja fitur pengaduan GovSmart?", "aplikasi"),
    ("Bagaimana cara melihat status laporan?", "aplikasi"),
    ("Bagaimana cara membatalkan pengaduan?", "aplikasi"),
    ("Berapa batas panjang pertanyaan chatbot?", "aplikasi"),
    ("Bagaimana cara mengganti password?", "aplikasi"),
    ("Apa yang dilakukan jika login gagal?", "aplikasi"),
    ("Bagaimana cara keluar dari akun?", "aplikasi"),
    ("Apakah foto bukti wajib diunggah?", "aplikasi"),
    ("Bagaimana cara menggunakan lokasi GPS?", "aplikasi"),
    ("Apa arti Negara Kesatuan Republik Indonesia?", "kenegaraan"),
    ("Kapan Proklamasi Kemerdekaan Indonesia dibacakan?", "kenegaraan"),
    ("Apa makna Bhinneka Tunggal Ika?", "kenegaraan"),
    ("Apa lambang negara Indonesia?", "kenegaraan"),
    ("Apa fungsi UUD 1945?", "kenegaraan"),
    ("Apa saja sila dalam Pancasila?", "kenegaraan"),
    ("Apa makna persatuan Indonesia?", "kenegaraan"),
    ("Apa arti bela negara?", "kenegaraan"),
    ("Siapa yang merumuskan dasar negara?", "kenegaraan"),
    ("Apa itu wawasan kebangsaan?", "kenegaraan"),
    ("Bagaimana cara daftar OSS?", "pemerintah"),
    ("Apa dokumen untuk izin usaha?", "pemerintah"),
    ("Bagaimana proses izin mendirikan bangunan?", "pemerintah"),
    ("Apa itu AMDAL?", "pemerintah"),
    ("Apa itu SPPL?", "pemerintah"),
    ("Bagaimana mengurus izin operasional?", "pemerintah"),
    ("Apa layanan Dinas Perhubungan?", "pemerintah"),
    ("Bagaimana melaporkan lampu jalan mati?", "pemerintah"),
    ("Bagaimana melaporkan drainase tersumbat?", "pemerintah"),
    ("Bagaimana melaporkan banjir?", "pemerintah"),
    ("Bagaimana mengurus bantuan sosial?", "pemerintah"),
    ("Apa syarat mendapatkan bantuan UMKM?", "pemerintah"),
    ("Bagaimana mengurus akta kelahiran?", "pemerintah"),
    ("Bagaimana mengurus akta kematian?", "pemerintah"),
    ("Bagaimana memperbaiki data KK?", "pemerintah"),
    ("Bagaimana cara daftar layanan kesehatan?", "pemerintah"),
    ("Apa itu layanan publik daerah?", "pemerintah"),
    ("Bagaimana cara mengajukan laporan warga?", "aplikasi"),
    ("Apakah laporan warga bisa dibatalkan?", "aplikasi"),
    ("Mengapa laporan saya belum diproses?", "aplikasi"),
    ("Bagaimana melihat dinas tujuan laporan?", "aplikasi"),
    ("Apa yang harus ditulis di isi laporan?", "aplikasi"),
    ("Apakah lokasi laporan wajib diisi?", "aplikasi"),
    ("Apa format foto bukti yang diterima?", "aplikasi"),
    ("Bagaimana jika lupa password akun?", "aplikasi"),
    ("Mengapa akun saya tidak bisa login?", "aplikasi"),
    ("Bagaimana cara mendaftar sebagai warga?", "aplikasi"),
    ("Apa tujuan dibuatnya GovSmart?", "aplikasi"),
    ("Apa hubungan Pancasila dan UUD 1945?", "kenegaraan"),
    ("Apa makna lambang Garuda Pancasila?", "kenegaraan"),
    ("Mengapa bahasa Indonesia menjadi bahasa negara?", "kenegaraan"),
    ("Apa arti persamaan kedudukan warga negara?", "kenegaraan"),
    ("Apa kewajiban warga negara?", "kenegaraan"),
    ("Apa hak warga negara menurut UUD?", "kenegaraan"),
    ("Apa makna Sumpah Pemuda?", "kenegaraan"),
    ("Apa tujuan Proklamasi Kemerdekaan?", "kenegaraan"),
    ("Apa yang dimaksud konstitusi?", "kenegaraan"),
    ("Bagaimana menjaga persatuan Indonesia?", "kenegaraan"),
    ("Bagaimana cara mengurus izin usaha online?", "pemerintah"),
    ("Apa perbedaan NIB dan izin usaha?", "pemerintah"),
    ("Bagaimana cara cek status perizinan?", "pemerintah"),
    ("Apa syarat izin praktik tenaga kesehatan?", "pemerintah"),
    ("Bagaimana mengurus izin lingkungan?", "pemerintah"),
    ("Apa yang dimaksud pelayanan terpadu?", "pemerintah"),
    ("Bagaimana cara mendapatkan informasi dinas?", "pemerintah"),
    ("Ke mana melapor jika ada pungutan liar?", "pemerintah"),
    ("Bagaimana melapor fasilitas umum rusak?", "pemerintah"),
    ("Bagaimana melapor pohon tumbang?", "pemerintah"),
    ("Bagaimana melapor sungai tercemar?", "pemerintah"),
    ("Bagaimana melapor jalan tergenang?", "pemerintah"),
    ("Bagaimana melapor jembatan rusak?", "pemerintah"),
    ("Bagaimana melapor lampu lalu lintas rusak?", "pemerintah"),
    ("Bagaimana melapor parkir liar?", "pemerintah"),
    ("Apa layanan Dinas Sosial?", "pemerintah"),
    ("Apa layanan Dinas Pendidikan?", "pemerintah"),
    ("Apa layanan Dinas Lingkungan Hidup?", "pemerintah"),
    ("Apa layanan Dinas Perhubungan?", "pemerintah"),
    ("Bagaimana cara mengirim pengaduan baru?", "aplikasi"),
    ("Apa yang terjadi setelah laporan dikirim?", "aplikasi"),
    ("Bagaimana mengetahui laporan sudah diterima?", "aplikasi"),
    ("Apa arti status diterima?", "aplikasi"),
    ("Apa arti status diproses?", "aplikasi"),
    ("Apa arti status selesai?", "aplikasi"),
    ("Apa arti status ditolak?", "aplikasi"),
    ("Apa arti status dibatalkan?", "aplikasi"),
    ("Berapa banyak riwayat laporan yang ditampilkan?", "aplikasi"),
    ("Apakah laporan tanpa foto bisa dikirim?", "aplikasi"),
    ("Apakah koordinat lokasi wajib diisi?", "aplikasi"),
    ("Bagaimana memilih dinas tujuan laporan?", "aplikasi"),
    ("Mengapa laporan diarahkan ke dinas tertentu?", "aplikasi"),
    ("Bagaimana memperbarui halaman laporan?", "aplikasi"),
    ("Apakah data NIK saya aman?", "aplikasi"),
    ("Bagaimana menjaga keamanan akun?", "aplikasi"),
    ("Apa yang dilakukan chatbot GovSmart?", "aplikasi"),
    ("Bagaimana menanyakan informasi kepada chatbot?", "aplikasi"),
    ("Mengapa jawaban chatbot memakai sumber?", "aplikasi"),
    ("Apa arti Negara Kesatuan?", "kenegaraan"),
    ("Apa tujuan negara Indonesia?", "kenegaraan"),
    ("Apa kedudukan Pancasila bagi negara?", "kenegaraan"),
    ("Apa isi sila pertama Pancasila?", "kenegaraan"),
    ("Apa isi sila kedua Pancasila?", "kenegaraan"),
    ("Apa isi sila ketiga Pancasila?", "kenegaraan"),
    ("Apa isi sila keempat Pancasila?", "kenegaraan"),
    ("Apa isi sila kelima Pancasila?", "kenegaraan"),
    ("Apa makna warna merah pada bendera?", "kenegaraan"),
    ("Apa makna warna putih pada bendera?", "kenegaraan"),
    ("Apa arti lambang Garuda?", "kenegaraan"),
    ("Apa makna semboyan Bhinneka Tunggal Ika?", "kenegaraan"),
    ("Apa yang dimaksud kedaulatan rakyat?", "kenegaraan"),
    ("Apa peran warga negara dalam demokrasi?", "kenegaraan"),
    ("Mengapa hukum dasar negara diperlukan?", "kenegaraan"),
    ("Apa perbedaan UUD dan undang-undang?", "kenegaraan"),
    ("Apa makna kemerdekaan bagi Indonesia?", "kenegaraan"),
    ("Apa peran bahasa Indonesia dalam persatuan?", "kenegaraan"),
    ("Apa itu identitas nasional?", "kenegaraan"),
    ("Bagaimana menerapkan nilai Pancasila?", "kenegaraan"),
]
_VARIANT_FORMS = [
    "{}", "Tolong jelaskan {}", "Saya mau tahu: {}", "Mohon info {}",
    "gmn {}", "brp {}", "apa syaratnya kalau {}", "bisa bantu {}",
    "{} ya?", "{} dong",
]
QUESTION_VARIANTS = []
_VARIANT_TYPOS = {
    "Tolong jelaskan": "Tlg jelaskan", "Bagaimana": "Bgmn", "Berapa": "Brp",
    "syarat": "syrat", "izin": "ijin", "pengaduan": "pngaduan",
    "aplikasi": "aplkasi", "Pancasila": "Pancsila", "Indonesia": "Indonesa",
    "Bagaimana": "Bgmn", "Apa": "Apaa", "cara": "cra", "melapor": "mlapor",
    "layanan": "layann", "negara": "negraa",
}
for _seed, _koleksi in _VARIANT_SEEDS:
    for _form in _VARIANT_FORMS:
        _q = _form.format(_seed)
        QUESTION_VARIANTS.append({"q": _q, "koleksi": _koleksi, "jenis": "normal"})
        _typo_q = _q
        for _wrong, _right in _VARIANT_TYPOS.items():
            if _wrong in _typo_q:
                _typo_q = _typo_q.replace(_wrong, _right)
                break
        if _typo_q != _q:
            QUESTION_VARIANTS.append({"q": _typo_q, "koleksi": _koleksi, "jenis": "typo"})

# EVAL keeps only questions with known expected documents; variants are a separate
# router/retriever smoke corpus and must not be counted as factual ground truth.
QUESTION_VARIANTS = QUESTION_VARIANTS[:400]


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
