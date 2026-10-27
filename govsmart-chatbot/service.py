import os
import re
import hmac
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import threading
from typing import Dict, Any
from dotenv import load_dotenv; load_dotenv()
# Masking regex
RE_NIK = re.compile(r"(?:\d[\s-]?){16}")  # Deteksi 16 digit, boleh ada spasi/tanda hubung
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

def mask_pii(text: str) -> str:
    # NIK
    def _masknik(m):
        nik = re.sub(r"[\s-]", "", m.group())
        return "[NIK]" if len(nik)==16 else m.group()
    masked = RE_NIK.sub(_masknik, text)
    # Email
    return RE_EMAIL.sub("[EMAIL]", masked)

SUMBER_KEYS = ["no", "judul", "konteks", "layanan", "halaman"]

def whitelist_result(res: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: res[k] for k in ("jawaban","intent","mode") if k in res}
    if "sumber" in res and isinstance(res["sumber"], list):
        out["sumber"] = [{k:v for k,v in s.items() if k in SUMBER_KEYS} for s in res["sumber"]]
    return out

# Semaphore concurrency limit
CONC = int(os.getenv("CHATBOT_MAX_CONCURRENCY", "2"))
_sema = threading.Semaphore(CONC)

TOKEN = os.getenv("CHATBOT_INTERNAL_TOKEN")
if not TOKEN:
    raise RuntimeError("CHATBOT_INTERNAL_TOKEN wajib di-set")


# Gunakan GovSmartChatbot jika tersedia, fallback Dummy hanya jika gagal
try:
    from scripts.chatbot import GovSmartChatbot
    _default_bot = GovSmartChatbot()
except Exception as e:
    print("[WARN] Gagal load GovSmartChatbot, pakai SmartFallbackChatbot. Error:", e)
    class SmartFallbackChatbot:
        def tanya(self, pertanyaan, pakai_llm=True):
            q = str(pertanyaan or "").lower()
            if any(k in q for k in ["bikin akun", "buat akun", "daftar", "registrasi", "register"]):
                jawaban = (
                    "Untuk membuat akun baru di GovSmart:\n"
                    "1. Klik menu 'Daftar Baru' pada halaman login.\n"
                    "2. Masukkan NIK (16 digit) dan Email aktif.\n"
                    "3. Buat Password (min. 8 karakter dengan huruf besar, huruf kecil, angka, dan simbol).\n"
                    "4. Tekan Daftar. Akun langsung aktif untuk login."
                )
                intent = "faq_registrasi_akun"
                layanan = "Layanan Akun GovSmart"
            elif any(k in q for k in ["login", "masuk", "password", "kata sandi"]):
                jawaban = "Gunakan Email atau NIK beserta password Anda pada halaman Masuk. Sesi login berlaku 24 jam."
                intent = "faq_login_akun"
                layanan = "Layanan Akun GovSmart"
            elif any(k in q for k in ["nib", "oss", "izin usaha", "umkm"]):
                jawaban = "Pendaftaran NIB untuk UMKM dapat dilakukan mandiri dan gratis via oss.go.id atau dibantu di loket DPMPTSP MPP Lamongan."
                intent = "faq_nib"
                layanan = "DPMPTSP Lamongan"
            elif any(k in q for k in ["ktp", "kk", "akta", "kia", "dukcapil", "pindah"]):
                jawaban = "Layanan Adminduk (KTP, KK, Akta) dilayani gratis di Disdukcapil Lamongan atau kantor kecamatan setempat."
                intent = "faq_adminduk"
                layanan = "Disdukcapil Lamongan"
            elif any(k in q for k in ["jalan", "lubang", "aspal", "jembatan"]):
                jawaban = "Kerusakan jalan kabupaten dan jembatan ditangani oleh Dinas PU Bina Marga. Laporkan melalui menu Buat Laporan dengan foto dan koordinat GPS."
                intent = "laporan_jalan"
                layanan = "Dinas PU Bina Marga"
            elif any(k in q for k in ["lampu", "pju", "rambu", "dishub"]):
                jawaban = "Lampu jalan (PJU) padam dan rambu lalu lintas ditangani Dinas Perhubungan Lamongan. Laporkan nama jalan dan nomor tiang lampu."
                intent = "laporan_pju"
                layanan = "Dinas Perhubungan"
            elif any(k in q for k in ["sampah", "tps", "kebersihan", "dlh"]):
                jawaban = "Tumpukan sampah liar dan kebersihan lingkungan ditangani Dinas Lingkungan Hidup (DLH) Lamongan. Kirim laporan di GovSmart."
                intent = "laporan_sampah"
                layanan = "Dinas Lingkungan Hidup"
            elif any(k in q for k in ["bansos", "pkh", "bpnt", "dinsos", "dtks"]):
                jawaban = "Bantuan sosial bersumber dari DTKS Kemensos RI dan diusulkan melalui musyawarah desa/kelurahan setempat sebelum verifikasi Dinas Sosial."
                intent = "faq_bansos"
                layanan = "Dinas Sosial"
            elif any(k in q for k in ["kesehatan", "puskesmas", "rsud", "bpjs"]):
                jawaban = "Pelayanan kesehatan dasar dilayani di Puskesmas kecamatan dan rujukan lanjutan di RSUD dr. Soegiri Lamongan dengan kepesertaan BPJS Kesehatan."
                intent = "faq_kesehatan"
                layanan = "Dinas Kesehatan"
            else:
                jawaban = (
                    "Untuk membuat laporan pengaduan fasilitas umum, pilih menu 'Buat Laporan' di GovSmart. "
                    "Sistem AI akan otomatis merutekan laporan Anda ke dinas terkait."
                )
                intent = "panduan_aplikasi"
                layanan = "GovSmart Administrator"

            return {
                "jawaban": jawaban,
                "intent": intent,
                "mode": "smart_fallback",
                "sumber": [{"no": 1, "judul": f"Panduan Resmi {layanan}", "konteks": "Pelayanan Terpadu Kabupaten Lamongan", "layanan": layanan, "halaman": "1"}]
            }
    _default_bot = SmartFallbackChatbot()

# Ubah DummyChatbot() ke load GovSmartChatbot() bila pipeline tersedia
def create_app(bot=None):
    app = FastAPI()
    chatbot = bot or _default_bot
    # ponytail: siap = index ada. Cek model LLM saat /ask, bukan di health.
    index_file = os.path.join(os.path.dirname(__file__), "data", "index", "index_meta.json")
    is_ready = os.path.isfile(index_file) or bot is not None

    @app.middleware("http")
    async def _limit(request:Request, call_next):
        if request.url.path=="/health":
            return await call_next(request)
        if not _sema.acquire(blocking=False):
            return JSONResponse({"kode":"TOO_MANY_REQUESTS","pesan":"Sistem sedang sibuk, coba lagi nanti.","fields":[]},429)
        try:
            return await call_next(request)
        finally:
            _sema.release()

    @app.get("/health")
    def health():
        return {"is_ready": is_ready}

    @app.post("/ask")
    def ask(payload:dict, request:Request):
        token = request.headers.get("X-Internal-Token")
        if not token or not hmac.compare_digest(token, TOKEN):
            raise HTTPException(401, detail={"kode": "UNAUTHORIZED", "pesan":"Token internal salah atau kosong.","fields":[]})
        q = payload.get("pertanyaan","")
        q = mask_pii(str(q).strip())
        if not (1 <= len(q) <= 500):
            return JSONResponse({"kode": "INVALID_INPUT", "pesan": "Pertanyaan wajib 1-500 karakter.", "fields": ["pertanyaan"]},422)
        try:
            hasil = chatbot.tanya(q)
        except Exception:
            return JSONResponse({"kode": "SERVICE_ERROR", "pesan": "Terjadi galat sistem.", "fields": []}, 503)
        hasil["jawaban"] = mask_pii(hasil.get("jawaban", ""))
        return whitelist_result(hasil)

    return app

app = create_app()
