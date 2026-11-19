#!/usr/bin/env python3
"""Tahap 4b - Retriever hybrid untuk chatbot GovSmart.

Pencarian = embedding (makna) + BM25 (kata kunci persis, mis. "Pasal 57", "KKPR", "NIB"),
digabung dengan Reciprocal Rank Fusion. Bisa difilter per koleksi (aplikasi / pemerintah / kenegaraan)
sesuai hasil intent router.

Pemakaian (dari root proyek):
    python scripts/retriever.py "berapa lama registrasi KKPR" --koleksi pemerintah -k 5
    python scripts/retriever.py --eval
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

JENIS_BOBOT = {"naskah_sejarah": 0.6, "faq": 1.15, "panduan": 1.15}
LAMPIRAN_OCR_BOBOT = 0.65
PRODUK_BOOST = 0.45
KONTEKS_BOOST = 0.35

STOP = set("yang dan di ke dari untuk dengan pada adalah itu ini apa berapa bagaimana saja atau dalam "
           "akan oleh ada saya bisa dapat apakah siapa kapan mengapa kenapa".split())

QUESTION_FRAME_STOP = {
    "cara", "caranya", "bagaimana", "gimana", "apa", "apakah", "siapa", "berapa",
    "kapan", "dimana", "kemana", "mana", "mengapa", "kenapa", "tolong", "mohon",
    "jelaskan", "info", "informasi", "arti", "artinya", "makna", "maksud", "dimaksud",
    "bisa", "bisakah", "dapat", "boleh", "harus", "mau", "ingin", "tahu", "cari",
    "buat", "membuat", "dibuatnya", "bikin", "membuka", "buka", "urus", "mengurus",
    "pakai", "memakai", "gunakan", "menggunakan", "lihat", "melihat", "cek", "mengecek",
    "terjadi", "dilakukan", "saja", "ya", "dong", "nih", "sih", "kan", "kok",
}


def tokenize(text):
    return [t for t in re.findall(r"\w+", text.lower()) if t not in STOP]


def stem_id(w: str) -> str:
    """Stemming ringan Bahasa Indonesia untuk menyamakan kata berimbuhan dengan kata dasarnya."""
    if len(w) <= 4 or w in {"kedinasan", "kemalingan", "kewarganegaraan"}:
        return w
    s = w
    for suf in ("kannya", "annya", "inya", "nya", "lah", "kah"):
        if suf == "inya" and s.endswith(("ainya", "uinya", "oinya")):
            continue
        if len(s) - len(suf) >= 4 and s.endswith(suf):
            s = s[:-len(suf)]
            break
    if len(s) >= 7 and s.endswith("kan") and not s.endswith("aikan"):
        s = s[:-3]
    elif len(s) >= 6 and s.endswith("an"):
        s = s[:-2]
    elif len(s) >= 6 and s.endswith("i") and not s.endswith("ai"):
        s = s[:-1]
    for pre in ("memper", "diper", "keber", "keter", "meng", "peng", "meny", "peny", "mem", "pem", "men", "pen", "ber", "ter", "per", "me", "pe", "di", "ke", "se"):
        if len(s) - len(pre) >= 4 and s.startswith(pre):
            s = s[len(pre):]
            break
    return s


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
    "dukcapil": "Dinas Kependudukan dan Pencatatan Sipil",
    "disdukcapil": "Dinas Kependudukan dan Pencatatan Sipil",
    "dishub": "Dinas Perhubungan Penerangan Jalan Umum",
    "dlh": "Dinas Lingkungan Hidup sampah kebersihan",
    "dinsos": "Dinas Sosial bantuan sosial DTKS PKH",
    "dinkes": "Dinas Kesehatan Puskesmas RSUD",
    "disdik": "Dinas Pendidikan sekolah beasiswa",
    "pju": "Penerangan Jalan Umum lampu jalan",
    "kia": "Kartu Identitas Anak",
    "kk": "Kartu Keluarga",
    "dtks": "Data Terpadu Kesejahteraan Sosial",
    "pkh": "Program Keluarga Harapan bantuan sosial",
    "bpnt": "Bantuan Pangan Non Tunai",
    "opd": "Organisasi Perangkat Daerah dinas",
    "rtr": "Rencana Tata Ruang",
    "bpupk": "Badan Penyelidik Usaha-usaha Persiapan Kemerdekaan Indonesia",
    "uud": "Undang-Undang Dasar Negara Republik Indonesia",
    "nkri": "Negara Kesatuan Republik Indonesia",
    "sila": "dasar Pancasila Ketuhanan Kemanusiaan Persatuan Kerakyatan Keadilan",
    "bela": "pembelaan pertahanan keamanan negara",
    "wawasan": "kebangsaan nasionalisme persatuan kesatuan",
    "sumpah": "pemuda bahasa persatuan",
    "pungutan": "ketertiban perda satpol",
    "operasional": "perizinan berusaha menunjang kegiatan usaha umku",
    "tersumbat": "drainase saluran air selokan banjir",
    "gps": "koordinat lokasi latitude longitude Gunakan Lokasi Saya",
    "keluar": "logout sesi login ulang keamanan akun",
    "tercemar": "pencemaran limbah polusi sampah lingkungan",
    "tergenang": "banjir drainase saluran air selokan jalan",
    "parkir": "lampu jalan rambu lalu lintas macet terminal Dinas Perhubungan",
    "tanpa": "wajib opsional mengisi foto bukti lokasi",
    "keamanan": "aman menjaga sesi login password hash dilindungi",
    "identitas": "bendera bahasa lambang negara lagu kebangsaan pemersatu eksistensi bangsa",
    "praktik": "praktek",
    "praktek": "praktik",
    "aman": "dilindungi keamanan pribadi hash password",
    "unggah": "diunggah foto bukti ukuran format",
    "nasional": "bangsa negara indonesia",
    "bantuan": "bansos sosial layanan pendampingan umkm",
    "sumber": "rujukan dokumen chatbot",
    "informasi": "panduan layanan pengaduan",
    "menghubungi": "dinas terkait pengaduan laporan",
}

QUERY_SYNONYMS = {
    "bikin": "buat membuat mendaftar pendaftaran",
    "buat": "bikin membuat mendaftar",
    "pakai": "menggunakan memakai panduan",
    "gunakan": "menggunakan memakai panduan",
    "menggunakan": "memakai panduan fitur",
    "biaya": "tarif retribusi gratis",
    "bayar": "biaya tarif retribusi",
    "lama": "jangka waktu hari",
    "syarat": "persyaratan dokumen",
    "persyaratan": "syarat",
    "urus": "mengurus pengurusan pelayanan pendaftaran",
    "mengurus": "urus pelayanan pendaftaran",
    "lapor": "melapor laporan pengaduan",
    "melapor": "lapor laporan pengaduan",
    "pengaduan": "laporan aduan",
    "mati": "padam rusak",
    "padam": "mati",
    "hilang": "rusak penggantian kehilangan",
    "edit": "mengedit mengubah menghapus",
    "hapus": "menghapus mengedit membatalkan",
    "batal": "membatalkan dibatalkan",
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
    tokens = dict.fromkeys(re.findall(r"\w+", (q + " " + q_norm).lower()))
    extra = [ALIAS[t] for t in tokens if t in ALIAS]
    syn = [QUERY_SYNONYMS[t] for t in tokens if t in QUERY_SYNONYMS]
    parts = extra + syn
    return q_norm + (" (" + "; ".join(parts) + ")" if parts else "")


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
        self.konteks_tok = [set(tokenize(c["konteks"])) if c.get("konteks") else set() for c in self.chunks]
        self.chunk_tokens = [set(tokenize(c["teks_embed"])) for c in self.chunks]
        self.chunk_stems = [{stem_id(t) for t in toks} for toks in self.chunk_tokens]
        self.corpus_vocab = set(ALIAS.keys()) | set(QUERY_SYNONYMS.keys()) | {
            "bpupk", "bpupki", "ppki", "sidang", "perumusan", "merumuskan",
            "dasar", "soekarno", "hatta", "yamin", "soepomo", "radjiman",
        }
        for c, toks in zip(self.chunks, self.chunk_tokens):
            if c["doc_id"] != "anri_naskah_sumber_bpupk_1945":
                self.corpus_vocab.update(toks)
        self.corpus_stems = {stem_id(t) for t in self.corpus_vocab}
        self.bobot = np.array([self._bobot(c) for c in self.chunks], dtype="float32")
        self._model = None

    @staticmethod
    def _bobot(c):
        w = JENIS_BOBOT.get(c["jenis"], 1.0)
        if c.get("sumber_ocr") and c.get("konteks", "").upper().startswith("LAMPIRAN"):
            w *= LAMPIRAN_OCR_BOBOT
        return w

    def _encode_query(self, q):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
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
        """-> list dict: chunk, skor (RRF x bobot), dense (cosine)."""
        q_norm = koreksi_teks(query)
        raw_toks = tokenize(q_norm)
        topic_toks = [t for t in raw_toks if t not in QUESTION_FRAME_STOP] or raw_toks
        topic_qt = set(topic_toks)
        alias_toks = [
            tok
            for t in dict.fromkeys(re.findall(r"\w+", (query + " " + q_norm).lower()))
            if t in ALIAS
            for tok in tokenize(ALIAS[t])
        ]
        primary_tokens = topic_toks + alias_toks
        expanded = expand_query(query)
        if koleksi is None:
            mask = np.ones(len(self.chunks), dtype=bool)
        else:
            mask = np.isin(self.koleksi, [koleksi] if isinstance(koleksi, str) else list(koleksi))
        dense = self._dense_scores(expanded)
        bm_primary = self.bm25.scores(primary_tokens)
        bm_syn = self.bm25.scores(tokenize(expanded))
        bm = np.where(bm_primary > 0, bm_primary + 0.35 * bm_syn, 0.0)
        dense_m = np.where(mask, dense, -np.inf)
        bm_m = np.where(mask, bm, -np.inf)

        fused = defaultdict(float)
        if np.any(dense > 0):
            for r, i in enumerate(np.argsort(-dense_m)[:pool]):
                if np.isfinite(dense_m[i]) and dense_m[i] > 0:
                    fused[int(i)] += 1.0 / (60 + r + 1)
        for r, i in enumerate(np.argsort(-bm_m)[:pool]):
            if np.isfinite(bm_m[i]) and bm_m[i] > 0:
                fused[int(i)] += 1.0 / (60 + r + 1)
        qt = set(tokenize(expanded))
        for i in fused:
            fused[i] *= float(self.bobot[i])
            pt = self.produk_tok[i]
            if pt:
                fused[i] *= 1 + PRODUK_BOOST * len(qt & pt) / len(pt)
            kt = self.konteks_tok[i]
            if kt and topic_qt:
                fused[i] *= 1 + KONTEKS_BOOST * len(topic_qt & kt) / max(len(topic_qt), 1)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        out = [{"chunk": self.chunks[i], "skor": fused[i], "dense": float(dense[i]), "idx": i} for i in top]
        if tetangga:
            seen = set(top)
            for i in top:
                for j in range(i + 1, min(i + 1 + tetangga, len(self.chunks))):
                    if self.chunks[j]["doc_id"] != self.chunks[i]["doc_id"]:
                        break
                    if j not in seen:
                        seen.add(j)
                        out.append({"chunk": self.chunks[j], "skor": 0.0, "dense": float(dense[j]), "tetangga": True, "idx": j})
        return out


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
    "Apa": "Apaa", "cara": "cra", "melapor": "mlapor",
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
