from typing import Tuple, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.models.department import Department

DEFAULT_DEPARTMENTS = [
    "Dinas Pendidikan",
    "Dinas Kesehatan",
    "Dinas Kependudukan dan Pencatatan Sipil",
    "Dinas Sosial",
    "Dinas Pemberdayaan Masyarakat dan Desa",
    "Dinas Pekerjaan Umum Bina Marga",
    "Dinas Pekerjaan Umum Sumber Daya Air",
    "Dinas Perumahan Rakyat, Kawasan Permukiman dan Cipta Karya",
    "Dinas Perhubungan",
    "Dinas Lingkungan Hidup",
    "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu",
    "Dinas Tenaga Kerja",
    "Dinas Perikanan",
    "Dinas Komunikasi dan Informatika",
    "Dinas Perpustakaan dan Kearsipan Daerah",
    "Dinas Satuan Polisi Pamong Praja",
    "Dinas Ketahanan Pangan dan Pertanian",
    "Dinas Koperasi, Perindustian, dan Perdagangan",
    "Dinas Kebudayaan, Pemuda dan Olahraga dan Pariwisata",
    "Dinas Pemberdayaan Perempuan, Perlindungan Anak dan Keluarga Berencana",
]

KEYWORDS_DEPT_MAP = {
    "Dinas Pendidikan": [
        "sekolah", "guru", "murid", "siswa", "beasiswa", "gedung sekolah",
        "seragam", "ijazah", "sd", "smp", "sma", "smk", "pendidikan", "belajar"
    ],
    "Dinas Kesehatan": [
        "posyandu", "puskesmas", "rumah sakit", "obat", "dokter", "ambulans",
        "penyakit", "demam", "dbd", "stunting", "kesehatan", "pasien", "vaksin"
    ],
    "Dinas Kependudukan dan Pencatatan Sipil": [
        "ktp", "e-ktp", "kk", "kartu keluarga", "akta", "suket", "pindahan",
        "akte kelahiran", "pernikahan", "perceraian", "kependudukan", "dukcapil"
    ],
    "Dinas Sosial": [
        "bansos", "bantuan sosial", "kemiskinan", "fakir miskin", "lansia",
        "disabilitas", "yatim", "anak terlantar", "pkh", "bpnt", "sosial"
    ],
    "Dinas Pemberdayaan Masyarakat dan Desa": [
        "desa", "dusun", "bumdes", "kelurahan", "dana desa", "musyawarah desa",
        "pemberdayaan", "masyarakat", "karang taruna", "posyandu desa"
    ],
    "Dinas Pekerjaan Umum Bina Marga": [
        "jalan rusak", "jalan ambruk", "pengerasan jalan", "berlubang",
        "lubang", "aspal", "trotoar", "infrastruktur", "jembatan", "bina marga",
    ],
    "Dinas Pekerjaan Umum Sumber Daya Air": [
        "drainase", "got", "selokan", "irigasi", "sungai", "banjir", "saluran air",
        "sumber daya air", "waduk", "dam", "tanggul", "pompa air",
        "longsor", "tanah", "lumpur", "lereng", "bencana alam",
    ],
    "Dinas Perumahan Rakyat, Kawasan Permukiman dan Cipta Karya": [
        "perumahan", "rumah", "permukiman", "rusun", "air bersih", "sanitasi",
        "cipta karya", "pdam", "pipanisasi", "pemukiman", "kavling"
    ],
    "Dinas Perhubungan": [
        "lampu lalu lintas", "traffic light", "rambu", "macet", "parkir",
        "terminal", "penerangan jalan", "pju", "angkutan", "transportasi"
    ],
    "Dinas Lingkungan Hidup": [
        "sampah", "pohon", "limbah", "bau", "polusi", "taman", "kebersihan",
        "lingkungan", "tps", "tempat sampah", "penghijauan", "pencemaran"
    ],
    "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu": [
        "izin", "perizinan", "umkm", "nib", "usaha", "pbg", "imb",
        "investasi", "ptsp", "dpmptsp", "siup", "tdp"
    ],
    "Dinas Tenaga Kerja": [
        "tenaga kerja", "buruh", "upah", "phk", "lowongan", "pengangguran",
        "pelatihan kerja", "disnaker", "tki", "bpjs ketenagakerjaan"
    ],
    "Dinas Perikanan": [
        "ikan", "nelayan", "tambak", "budidaya", "hasil laut", "kapal",
        "perikanan", "kolam ikan", "udang", "bandeng"
    ],
    "Dinas Komunikasi dan Informatika": [
        "internet", "wifi", "jaringan", "sinyal", "kominfo", "website",
        "aplikasi", "layanan online", "sistem informasi", "data", "siber"
    ],
    "Dinas Perpustakaan dan Kearsipan Daerah": [
        "perpustakaan", "buku", "arsip", "dokumen", "literasi",
        "koleksi buku", "pustakawan", "kearsipan"
    ],
    "Dinas Satuan Polisi Pamong Praja": [
        "pedagang kaki lima", "pkl", "ketertiban", "kebisingan", "razia",
        "satpol", "penertiban", "pelanggaran perda", "liar", "bangunan liar"
    ],
    "Dinas Ketahanan Pangan dan Pertanian": [
        "pangan", "pertanian", "sawah", "padi", "pupuk", "hama", "petani",
        "kebun", "hortikultura", "tanaman", "ketahanan pangan", "gabah"
    ],
    "Dinas Koperasi, Perindustrian, dan Perdagangan": [
        "koperasi", "industri", "perdagangan", "pasar", "pedagang",
        "ukm", "usaha kecil", "toko", "pabrik", "produksi", "distribusi"
    ],
    "Dinas Kebudayaan, Pemuda dan Olahraga dan Pariwisata": [
        "budaya", "seni", "wisata", "pariwisata", "olahraga", "pemuda",
        "stadion", "lapangan", "festival", "kesenian", "destinasi wisata"
    ],
    "Dinas Pemberdayaan Perempuan, Perlindungan Anak dan Keluarga Berencana": [
        "perempuan", "anak", "kekerasan", "kdrt", "kb", "keluarga berencana",
        "perlindungan anak", "bkb", "posyandu balita", "gender"
    ],
}

EMERGENCY_KEYWORDS = [
    "darurat", "kebakaran", "ambruk", "longsor", "korban", "bahaya",
    "kecelakaan", "rusak parah", "putus", "meledak", "banjir bandang", "mati"
]

IMPORTANT_KEYWORDS = [
    "penting", "mendesak", "segera", "mengganggu", "parah",
    "bau menyengat", "macet total", "mogok", "bocor", "rusak"
]

def analyze_report_ai(judul: str, isi: str, db: Session) -> Tuple[Optional[int], str]:
    text_lower = f"{judul} {isi}".lower()
    import re
    tokens = set(re.findall(r"\b[a-z]+\b", text_lower))  # single-word tokens for typo matching

    # 1. Determine Urgency (substring match, robust for multi-word)
    urgensi = "normal"
    if any(word in text_lower for word in EMERGENCY_KEYWORDS):
        urgensi = "darurat"
    elif any(word in text_lower for word in IMPORTANT_KEYWORDS):
        urgensi = "penting"

    # 2. Determine Department via Smart Routing
    #    Match keywords via substring. For single-word keywords, also apply fuzzy
    #    matching (cutoff 0.8) to tolerate typos (e.g. "smpah" -> "sampah").
    #    Multi-word keywords are matched by substring only (fuzzy on phrases is noisy).
    from difflib import get_close_matches
    best_dept_name = None
    max_matches = 0

    for dept_name, keywords in KEYWORDS_DEPT_MAP.items():
        matches = 0
        for kw in keywords:
            if kw in text_lower:
                matches += 1
            elif " " not in kw and len(kw) <= 6:
                # single-word keyword (short only to avoid morphologically noisy matches): fuzzy match
                for tok in tokens:
                    if get_close_matches(tok, [kw], n=1, cutoff=0.8):
                        matches += 1
                        break
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
        return ("Laporan kerusakan jalan dan fasilitas umum akan diteruskan langsung ke Dinas Pekerjaan Umum Bina Marga. "
                "Pastikan Anda menyertakan detail lokasi (kecamatan/desa) dan foto pendukung jika ada.")
    else:
        return ("Terima kasih telah menghubungi Asisten Virtual GovSmart. "
                "Saya dapat membantu Anda memberikan informasi layanan publik, syarat perizinan UMKM, administrasi kependudukan, serta panduan pengaduan warga. Ada yang bisa saya bantu lebih detail?")
