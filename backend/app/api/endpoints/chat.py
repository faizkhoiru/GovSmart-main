# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Request, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.privacy import mask_pii
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryOut
# pyrefly: ignore [missing-import]
import httpx
import time
from collections import defaultdict
from app.crud import chat as crud_chat

router = APIRouter()

RATE_LIMIT = getattr(settings, "CHAT_RATE_LIMIT_PER_MINUTE", 20)
WINDOW = 60
rl_state = defaultdict(list)

async def limited_user(user_id):
    now = time.time()
    window_start = now - WINDOW
    hits = rl_state[user_id]
    rl_state[user_id] = [t for t in hits if t > window_start]
    if RATE_LIMIT > 0 and len(rl_state[user_id]) >= RATE_LIMIT:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"kode": "RATE_LIMITED", "pesan": f"Maks {RATE_LIMIT}/menit", "fields": [], "retry_after": WINDOW},
        )
    rl_state[user_id].append(now)

def generate_builtin_chatbot_response(pertanyaan: str) -> dict:
    q = pertanyaan.lower()

    if any(k in q for k in ["halo", "hai", "assalamu", "selamat", "pagi", "siang", "sore", "malam"]):
        jawaban = (
            "Halo! Saya asisten virtual cerdas GovSmart Kabupaten Lamongan. "
            "Saya siap membantu Anda seputar informasi layanan publik Pemkab Lamongan, panduan pelaporan pengaduan, "
            "serta persyaratan administrasi kependudukan dan perizinan. Ada yang bisa saya bantu hari ini?"
        )
        intent = "sapaan"
        layanan = "Layanan Terpadu GovSmart"
    elif any(k in q for k in ["nib", "oss", "izin usaha", "umkm", "usaha mikro", "siup", "dagang"]):
        jawaban = (
            "Untuk pembuatan Nomor Induk Berusaha (NIB) bagi pelaku UMKM di Kabupaten Lamongan, "
            "Anda dapat mendaftar mandiri secara gratis melalui sistem Online Single Submission (OSS) di oss.go.id. "
            "Persyaratan: KTP, KK, NPWP (opsional), dan nomor WhatsApp/email aktif. "
            "Jika memerlukan pendampingan tatap muka, Anda dapat mendatangi loket pelayanan DPMPTSP Kabupaten Lamongan."
        )
        intent = "faq_nib"
        layanan = "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu"
    elif any(k in q for k in ["ktp", "kk", "kartu keluarga", "akta", "kia", "pindah", "dukcapil", "adminduk", "capil"]):
        jawaban = (
            "Pengurusan dokumen kependudukan (KTP-el baru/rusak/hilang, Kartu Keluarga, Akta Kelahiran, dan Surat Pindah) "
            "dilayani oleh Dinas Kependudukan dan Pencatatan Sipil (Disdukcapil) Kabupaten Lamongan. "
            "Semua layanan adminduk gratis/tanpa pungutan biaya. Anda dapat mengurusnya langsung di kantor Disdukcapil "
            "atau melalui loket pelayanan adminduk kecamatan dengan membawa berkas pendukung."
        )
        intent = "faq_adminduk"
        layanan = "Dinas Kependudukan dan Pencatatan Sipil"
    elif any(k in q for k in ["jalan", "lubang", "rusak", "aspal", "jembatan", "bina marga"]):
        jawaban = (
            "Laporan mengenai jalan rusak, jalan berlubang, atau kerusakan jembatan di wilayah Kabupaten Lamongan "
            "dapat diajukan melalui fitur 'Buat Laporan' di aplikasi GovSmart. "
            "Sertakan foto kondisi jalan dan aktifkan penanda lokasi GPS. "
            "Laporan akan otomatis diverifikasi dan diteruskan ke Dinas Pekerjaan Umum Bina Marga untuk perbaikan."
        )
        intent = "laporan_jalan_rusak"
        layanan = "Dinas Pekerjaan Umum Bina Marga"
    elif any(k in q for k in ["lampu", "pju", "penerangan", "dishub", "rambu", "lalu lintas"]):
        jawaban = (
            "Laporan terkait Penerangan Jalan Umum (PJU) mati, rambu lalu lintas rusak, atau penerangan jalan "
            "dikelola oleh Dinas Perhubungan Kabupaten Lamongan. "
            "Silakan buat laporan dengan menyertakan titik lokasi tiang lampu agar petugas teknis Dishub dapat segera mengganti komponen lampu."
        )
        intent = "laporan_pju"
        layanan = "Dinas Perhubungan"
    elif any(k in q for k in ["sampah", "tps", "tpa", "kebersihan", "limbah", "sungai", "lingkungan", "dlh"]):
        jawaban = (
            "Pengaduan terkait tumpukan sampah liar, pembersihan saluran, dan lingkungan hidup ditangani oleh "
            "Dinas Lingkungan Hidup (DLH) Kabupaten Lamongan. "
            "Anda dapat membuat laporan pengaduan di aplikasi ini dengan melampirkan foto tumpukan sampah dan alamat jelas untuk jadwal pengangkutan armada kebersihan."
        )
        intent = "laporan_sampah"
        layanan = "Dinas Lingkungan Hidup"
    elif any(k in q for k in ["bansos", "pkh", "bpnt", "bantuan", "dtks", "miskin", "dinsos"]):
        jawaban = (
            "Penyaluran bantuan sosial (PKH, BPNT, atau bansos asistensi) mengacu pada Data Terpadu Kesejahteraan Sosial (DTKS) "
            "yang dikelola oleh Dinas Sosial Kabupaten Lamongan. Pendaftaran dan verifikasi usulan kelayakan keluarga "
            "dilakukan melalui musyawarah desa/kelurahan setempat sebelum diajukan ke dinas."
        )
        intent = "faq_bansos"
        layanan = "Dinas Sosial"
    elif any(k in q for k in ["sehat", "kesehatan", "bpjs", "puskesmas", "rsud", "dokter", "obat"]):
        jawaban = (
            "Layanan kesehatan masyarakat difasilitasi oleh Dinas Kesehatan Kabupaten Lamongan melalui Puskesmas di setiap kecamatan "
            "dan RSUD dr. Soegiri Lamongan. Warga dapat memanfaatkan kartu BPJS Kesehatan / KIS untuk mendapatkan pemeriksaan berjenjang."
        )
        intent = "faq_kesehatan"
        layanan = "Dinas Kesehatan"
    elif any(k in q for k in ["lapor", "pengaduan", "cara", "adukan", "fitur"]):
        jawaban = (
            "Panduan menyampaikan pengaduan di GovSmart:\n"
            "1. Masuk ke akun Anda dan pilih menu 'Buat Laporan'\n"
            "2. Isi judul dan uraian pengaduan secara lengkap\n"
            "3. Unggah foto bukti di lokasi kejadian\n"
            "4. Pilih titik lokasi pada peta interaktif\n"
            "5. AI GovSmart akan menganalisis teks laporan dan secara otomatis merutekannya ke dinas yang berwenang."
        )
        intent = "panduan_aplikasi"
        layanan = "GovSmart Administrator"
    else:
        jawaban = (
            f"Terima kasih atas pertanyaan Anda seputar '{pertanyaan}'. "
            "Layanan publik Pemerintah Kabupaten Lamongan kini terintegrasi di GovSmart. "
            "Jika ini merupakan keluhan atau pengaduan fasilitas umum, Anda dapat menggunakan menu 'Buat Laporan'. "
            "Untuk informasi prosedur kedinasan lainnya, Anda juga dapat mengunjungi kantor dinas terkait atau MPP Lamongan."
        )
        intent = "tanya_umum"
        layanan = "Pemerintah Kabupaten Lamongan"

    return {
        "jawaban": jawaban,
        "intent": intent,
        "mode": "asisten_cerdas",
        "sumber": [
            {
                "no": 1,
                "judul": f"Panduan Pelayanan Publik {layanan}",
                "konteks": "Pusat Informasi dan Pengaduan Terpadu Pemerintah Kabupaten Lamongan",
                "layanan": layanan,
                "halaman": "1",
            }
        ],
    }


@router.post("/", response_model=ChatResponse, status_code=200)
async def ask_chatbot(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    user_id = current_user.id
    await limited_user(user_id)
    pertanyaan = mask_pii(payload.get_query())
    if not (1 <= len(pertanyaan) <= 500):
        raise HTTPException(422, detail="Pertanyaan wajib 1-500 karakter.")
    db.rollback()  # kunci: rolling sesi supaya pool DB tidak hold selama await

    body = None
    chat_url = settings.CHATBOT_URL + "/ask"
    headers = {"X-Internal-Token": settings.CHATBOT_INTERNAL_TOKEN}
    timeout = getattr(settings, "CHATBOT_TIMEOUT", 180)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(chat_url, json={"pertanyaan": pertanyaan}, headers=headers)
            if resp.status_code == 200:
                body = resp.json()
            elif resp.status_code == 422:
                raise HTTPException(422, detail=resp.json())
            elif resp.status_code == 429:
                raise HTTPException(429, detail={"kode": "CHATBOT_BUSY", "pesan": "Chatbot sedang sibuk.", "fields": [], "retry_after": 5})
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        import logging
        logging.getLogger(__name__).warning(f"External chatbot unavailable, falling back to built-in knowledge: {exc}")

    # Fallback ke asisten cerdas bawaan jika service eksternal belum aktif atau tidak merespons
    if not body:
        body = generate_builtin_chatbot_response(pertanyaan)

    jawaban = mask_pii(body.get("jawaban", ""))[:2000]
    crud_chat.create(db, user_id=user_id, prompt=pertanyaan, response=jawaban)
    chat_res = {k: body[k] for k in ("jawaban", "intent", "mode") if k in body}
    if "sumber" in body:
        chat_res["sumber"] = [
            {k: v for k, v in sumber.items() if k in ["no", "judul", "konteks", "layanan", "halaman"]}
            for sumber in body["sumber"]
        ]
    return chat_res

@router.get("/history", response_model=ChatHistoryOut)
def chat_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    limit = min(100, max(1, limit))
    rows = crud_chat.history(db, user_id=current_user.id, limit=limit, offset=offset)
    return {"results": rows, "count": len(rows)}

@router.delete("/history", status_code=204)
def chat_clear_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    crud_chat.clear_history(db, user_id=current_user.id)
    return None

