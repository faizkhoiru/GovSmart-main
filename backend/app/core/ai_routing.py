from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.department import Department

DEFAULT_DEPARTMENTS = [
    "Dinas Pekerjaan Umum & Penataan Ruang",
    "Dinas Lingkungan Hidup",
    "Dinas Kesehatan",
    "Dinas Perhubungan",
    "Dinas Penanaman Modal & PTSP",
    "Dinas Satuan Polisi Pamong Praja",
    "Dinas Pendidikan",
    "Dinas Kependudukan & Pencatatan Sipil"
]

KEYWORDS_DEPT_MAP = {
    "Dinas Pekerjaan Umum & Penataan Ruang": [
        "jalan", "jembatan", "lubang", "trotoar", "aspal", "drainase", "got", "selokan", "bangunan", "infrastruktur"
    ],
    "Dinas Lingkungan Hidup": [
        "sampah", "pohon", "limbah", "bau", "polusi", "taman", "kebersihan", "banjir"
    ],
    "Dinas Kesehatan": [
        "posyandu", "puskesmas", "rumah sakit", "obat", "dokter", "ambulans", "penyakit", "demam", "dbd", "stunting"
    ],
    "Dinas Perhubungan": [
        "lampu lalu lintas", "traffic light", "rambu", "macet", "parkir", "terminal", "penerangan jalan", "pju"
    ],
    "Dinas Penanaman Modal & PTSP": [
        "izin", "perizinan", "umkm", "nib", "usaha", "pbg", "imb", "investasi"
    ],
    "Dinas Satuan Polisi Pamong Praja": [
        "pedagang kaki lima", "pkl", "ketertiban", "kebisingan", "razia", "satpol"
    ],
    "Dinas Pendidikan": [
        "sekolah", "guru", "beasiswa", "gedung sekolah", "seragam", "ijazah"
    ],
    "Dinas Kependudukan & Pencatatan Sipil": [
        "ktp", "e-ktp", "kk", "kartu keluarga", "akta", "suket", "pindahan"
    ]
}

EMERGENCY_KEYWORDS = [
    "darurat", "kebakaran", "ambruk", "longsor", "korban", "bahaya", "kecelakaan", "rusak parah", "putus", "meledak"
]

IMPORTANT_KEYWORDS = [
    "penting", "mendesak", "segera", "mengganggu", "parah", "bau menyengat", "macet total"
]

def analyze_report_ai(judul: str, isi: str, db: Session) -> Tuple[Optional[int], str]:
    text_lower = f"{judul} {isi}".lower()

    # 1. Determine Urgency
    urgensi = "normal"
    if any(word in text_lower for word in EMERGENCY_KEYWORDS):
        urgensi = "darurat"
    elif any(word in text_lower for word in IMPORTANT_KEYWORDS):
        urgensi = "penting"

    # 2. Determine Department via Smart Routing
    best_dept_name = None
    max_matches = 0

    for dept_name, keywords in KEYWORDS_DEPT_MAP.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > max_matches:
            max_matches = matches
            best_dept_name = dept_name

    dept_id = None
    if best_dept_name:
        dept_obj = db.query(Department).filter(Department.nama_dinas == best_dept_name).first()
        if dept_obj:
            dept_id = dept_obj.id

    return dept_id, urgensi

def generate_ai_chatbot_response(prompt: str) -> str:
    p_lower = prompt.lower()
    
    if "umkm" in p_lower or "nib" in p_lower or "izin usaha" in p_lower:
        return ("Untuk pembuatan NIB (Nomor Induk Berusaha) bagi UMKM di Kabupaten Lamongan, Anda dapat mendaftar secara online via OSS (oss.go.id). "
                "Persyaratan: NIK KTP, Email aktif, dan No. HP. Pelayanan tatap muka dapat diakses di Dinas Penanaman Modal & PTSP.")
    elif "ktp" in p_lower or "kk" in p_lower or "akta" in p_lower:
        return ("Layanan e-KTP dan Kartu Keluarga dapat diurus melalui kantor Kecamatan setempat atau Disdukcapil. "
                "Persyaratan pembuatan e-KTP baru: Fotokopi KK dan berusia minimal 17 tahun. Bebas biaya (GRATIS).")
    elif "lapor" in p_lower or "pengaduan" in p_lower:
        return ("Anda dapat membuat laporan pengaduan melalui portal GovSmart pada menu 'Buat Laporan'. "
                "Sistem AI kami akan secara otomatis meneruskan laporan Anda ke dinas terkait dan menganalisis tingkat urgensinya.")
    elif "jalan" in p_lower or "rusak" in p_lower or "infrastruktur" in p_lower:
        return ("Laporan kerusakan jalan dan fasilitas umum akan diteruskan langsung ke Dinas Pekerjaan Umum & Penataan Ruang. "
                "Pastikan Anda menyertakan detail lokasi (kecamatan/desa) dan foto pendukung jika ada.")
    else:
        return ("Terima kasih telah menghubungi Asisten Virtual GovSmart. "
                "Saya dapat membantu Anda memberikan informasi layanan publik, syarat perizinan UMKM, administrasi kependudukan, serta panduan pengaduan warga. Ada yang bisa saya bantu lebih detail?")
