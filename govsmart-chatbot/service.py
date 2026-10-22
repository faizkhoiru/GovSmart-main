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
    print("[WARN] Gagal load GovSmartChatbot, pakai DummyChatbot. Error:", e)
    class DummyChatbot:
        def tanya(self, pertanyaan, pakai_llm=True):
            return {
                "jawaban": "Proses registrasi KKPR maksimal 5 hari; persetujuan 10 hari.",
                "intent": "faq_kkpr",
                "mode": "ekstraktif",
                "sumber": [{"no":1,"judul":"Panduan KKPR","konteks":"Registrasi KKPR","layanan":"Dinas Tata Ruang","halaman":"12"}]
            }
    _default_bot = DummyChatbot()

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
