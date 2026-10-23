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
        "sekolah", "sekolahh", "guru", "gruru", "murid", "siswa", "beasiswa", "beasiswaa", "gedung sekolah",
        "seragam", "ijazah", "ijazahh", "sd", "smp", "sma", "smk", "pendidikan", "pendidkan", "belajar",
        "kampus", "universitas", "mahasiswa", "mhs", "dosen", "kuliah", "kuliah", "fakultas", "sekolahan", "sekolah rusak",
        "ruang kelas", "kelas", "gedung kuliah", "paud", "tk", "madrasah",
        "fasilitas kampus", "fasilitas sekolah", "fasilitas pendidikan", "akademik",
        "buku pelajaran", "bop", "bosda", "dana bos", "tawuran pelajar"
    ],
    "Dinas Kesehatan": [
        "posyandu", "puskesmas", "puskes", "rumah sakit", "rumahsakit", "obat", "dokter", "dokterr", "ambulans",
        "penyakit", "demam", "dbd", "stunting", "kesehatan", "kesehtan", "pasien", "vaksin",
        "bidan", "perawat", "bpjs kesehatan", "bpjs", "fasilitas kesehatan", "faskes", "puskes", "rs", "rumahsakit", "kesehatan warga",
        "gizi buruk", "wabah", "medis", "imunisasi", "apotek", "infeksi", "virus",
        "diare", "poliklinik", "tenaga medis", "pelayanan medis", "igd"
    ],
    "Dinas Kependudukan dan Pencatatan Sipil": [
        "ktp", "e-ktp", "kk", "kartu keluarga", "akta", "suket", "pindahan",
        "akte kelahiran", "pernikahan", "perceraian", "kependudukan", "dukcapil",
        "akte kematian", "kia", "kartu identitas anak", "legalisir", "nik", "ktp hilang", "ktp rusak", "kk hilang", "kk rusak", "dukcapil", "adminduk",
        "domisili", "surat pindah", "identitas kependudukan", "ikd", "capil", "catatan sipil", "akta lahir", "akta kematian"
    ],
    "Dinas Sosial": [
        "bansos", "bantuan sosial", "kemiskinan", "fakir miskin", "lansia",
        "disabilitas", "yatim", "anak terlantar", "pkh", "bpnt", "sosial",
        "gelandangan", "pengemis", "gepeng", "panti asuhan", "bantuan bencana",
        "keluarga prasejahtera", "tuna wisma", "orang terlantar", "sembako", "bantuan", "bantuan warga", "kartu indonesia sehat", "kip", "penerima bansos"
    ],
    "Dinas Pemberdayaan Masyarakat dan Desa": [
        "desa", "dusun", "bumdes", "kelurahan", "dana desa", "musyawarah desa",
        "pemberdayaan", "masyarakat", "karang taruna", "posyandu desa", "kepala desa",
        "kades", "bpd", "perangkat desa", "rt", "rw", "pamong desa", "balai desa",
        "warga desa", "aparat desa"
    ],
    "Dinas Pekerjaan Umum Bina Marga": [
        "jalan rusak", "jalan ambruk", "pengerasan jalan", "berlubang",
        "lubang", "aspal", "trotoar", "infrastruktur", "jembatan", "bina marga",
        "jalanan", "jalan raya", "jembatan rusak", "jembatan ambruk", "jalan putus", "jalan rusak parah", "jalan berlubang", "jalan jelek", "aspal rusak", "akses jalan",
        "jalan amblas", "jalan ambles", "jalan retak", "jalan cor", "jalan bolong",
        "gorong-gorong jalan", "jalan kabupaten"
    ],
    "Dinas Pekerjaan Umum Sumber Daya Air": [
        "drainase", "got", "selokan", "irigasi", "sungai", "banjir", "saluran air",
        "sumber daya air", "waduk", "dam", "tanggul", "pompa air",
        "longsor", "tanah", "lumpur", "lereng", "bencana alam", "tanah longsor",
        "abrasi", "tanggul jebol", "kali", "rawa", "genangan air", "saluran pembuangan", "banjir rumah", "banjir jalan", "air meluap", "sungai meluap", "got mampet", "selokan mampet",
        "kali mampet", "erosi", "pintu air"
    ],
    "Dinas Perumahan Rakyat, Kawasan Permukiman dan Cipta Karya": [
        "perumahan", "rumah", "permukiman", "rusun", "air bersih", "sanitasi",
        "cipta karya", "pdam", "pipanisasi", "pemukiman", "kavling", "gedung",
        "bangunan roboh", "septic tank", "mck", "saluran limbah rumah tangga",
        "bedah rumah", "rutilahu", "rumah kumuh", "bangunan rusak"
    ],
    "Dinas Perhubungan": [
        "lampu lalu lintas", "traffic light", "rambu", "macet", "parkir",
        "terminal", "penerangan jalan", "pju", "angkutan", "transportasi",
        "marka jalan", "bus", "angkot", "juru parkir", "lampu jalan",
        "penerangan jalan umum", "pelabuhan", "halte", "kemacetan", "uji kir"
    ],
    "Dinas Lingkungan Hidup": [
        "sampah", "pohon", "limbah", "bau", "polusi", "taman", "kebersihan",
        "lingkungan", "tps", "tempat sampah", "penghijauan", "pencemaran",
        "pohon tumbang", "dahan patah", "tpa", "sampah menumpuk", "limbah pabrik",
        "sungai kotor", "tumpukan sampah", "bak sampah"
    ],
    "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu": [
        "izin", "perizinan", "umkm", "nib", "usaha", "pbg", "imb",
        "investasi", "ptsp", "dpmptsp", "siup", "tdp", "izin usaha", "oss",
        "izin mendirikan bangunan", "izin operasional"
    ],
    "Dinas Tenaga Kerja": [
        "tenaga kerja", "buruh", "upah", "phk", "lowongan", "pengangguran",
        "pelatihan kerja", "disnaker", "tki", "bpjs ketenagakerjaan", "pesangon",
        "umr", "umk", "gaji", "ketenagakerjaan", "blk", "magang", "pekerja migran"
    ],
    "Dinas Perikanan": [
        "ikan", "nelayan", "tambak", "budidaya", "hasil laut", "kapal",
        "perikanan", "kolam ikan", "udang", "bandeng", "bibit ikan", "pakan ikan",
        "tangkapan laut", "perahu nelayan", "tpi", "tempat pelelangan ikan"
    ],
    "Dinas Komunikasi dan Informatika": [
        "internet", "wifi", "jaringan", "sinyal", "kominfo", "website",
        "aplikasi", "layanan online", "sistem informasi", "data", "siber",
        "hoaks", "server", "blank spot", "tower", "tiang internet", "kabel fiber"
    ],
    "Dinas Perpustakaan dan Kearsipan Daerah": [
        "perpustakaan", "buku", "arsip", "dokumen", "literasi",
        "koleksi buku", "pustakawan", "kearsipan", "perpustakaan keliling",
        "pojok baca", "minat baca", "ruang baca"
    ],
    "Dinas Satuan Polisi Pamong Praja": [
        "pedagang kaki lima", "pkl", "ketertiban", "kebisingan", "razia",
        "satpol", "penertiban", "pelanggaran perda", "liar", "bangunan liar",
        "kebakaran", "kebkaran", "kebakran", "kebakaran rumah", "kebakaran gedung", "terbakar", "damkar", "pemadam kebakaran", "pemadam",
        "api", "hangus", "tawuran", "miras", "gangguan ketertiban", "prostitusi"
    ],
    "Dinas Ketahanan Pangan dan Pertanian": [
        "pangan", "pertanian", "sawah", "padi", "pupuk", "hama", "petani",
        "kebun", "hortikultura", "tanaman", "ketahanan pangan", "gabah",
        "panen", "irigasi sawah", "ternak", "sapi", "kambing", "unggas", "gagal panen"
    ],
    "Dinas Koperasi, Perindustian, dan Perdagangan": [
        "koperasi", "industri", "perdagangan", "pasar", "pedagang",
        "ukm", "usaha kecil", "toko", "pabrik", "produksi", "distribusi",
        "harga sembako", "minyak goreng", "beras mahal", "timbangan", "operasi pasar"
    ],
    "Dinas Kebudayaan, Pemuda dan Olahraga dan Pariwisata": [
        "budaya", "seni", "wisata", "pariwisata", "olahraga", "pemuda",
        "stadion", "lapangan", "festival", "kesenian", "destinasi wisata",
        "cagar budaya", "museum", "event pemuda", "tempat rekreasi"
    ],
    "Dinas Pemberdayaan Perempuan, Perlindungan Anak dan Keluarga Berencana": [
        "perempuan", "anak", "kekerasan", "kdrt", "kb", "keluarga berencana",
        "perlindungan anak", "bkb", "posyandu balita", "gender", "pelecehan",
        "trafficking", "eksploitasi anak", "ibu hamil", "pernikahan dini"
    ],
}

EMERGENCY_KEYWORDS = [
    "darurat", "kebakaran", "ambruk", "longsor", "korban", "bahaya",
    "kecelakaan", "rusak parah", "putus", "meledak", "banjir bandang", "mati",
    "terbakar", "tenggelam", "tersengat", "amblas", "gas bocor", "runtuh", "ledakan"
]

IMPORTANT_KEYWORDS = [
    "penting", "mendesak", "segera", "mengganggu", "parah",
    "bau menyengat", "macet total", "mogok", "bocor", "rusak"
]

def analyze_report_ai(judul: str, isi: str, db: Session) -> Tuple[Optional[int], str]:
    text_lower = f"{judul} {isi}".lower()
    import re
    tokens = set(re.findall(r"\b[a-z]+\b", text_lower))  # single-word tokens for exact and typo matching
    # Common typos only; avoid broad correction that can misroute reports.
    typo_aliases = {
        "kebkaran": "kebakaran", "kebakran": "kebakaran", "terbakarrr": "terbakar",
        "kesehtan": "kesehatan", "kesehataan": "kesehatan", "puskes": "puskesmas",
        "sekolahh": "sekolah", "pendidkan": "pendidikan", "beasiswaa": "beasiswa",
        "dokterr": "dokter", "jalanann": "jalanan", "berlubng": "berlubang",
        "sampahh": "sampah", "lingkungn": "lingkungan", "banjirr": "banjir",
        "perizinan": "perizinan", "perijinan": "perizinan", "dukcapill": "dukcapil",
    }
    tokens.update(typo_aliases[token] for token in list(tokens) if token in typo_aliases)

    # 1. Determine Urgency (substring match, robust for multi-word)
    urgensi = "normal"
    if any(word in text_lower for word in EMERGENCY_KEYWORDS):
        urgensi = "darurat"
    elif any(word in text_lower for word in IMPORTANT_KEYWORDS):
        urgensi = "penting"

    # 2. Determine Department via Smart Routing
    #    Phrase keywords (with space): substring in text_lower.
    #    Single-word keywords: exact token match, or fuzzy match (cutoff 0.85, len >= 5) to tolerate typos.
    from difflib import get_close_matches
    best_dept_name = None
    max_matches = 0

    for dept_name, keywords in KEYWORDS_DEPT_MAP.items():
        matches = 0
        for kw in keywords:
            if " " in kw:
                if kw in text_lower:
                    matches += 1
            else:
                if kw in tokens:
                    matches += 1
                elif len(kw) >= 5:
                    for tok in tokens:
                        if abs(len(tok) - len(kw)) <= 1 and get_close_matches(tok, [kw], n=1, cutoff=0.85):
                            matches += 1
                            break
        if matches > max_matches:
            max_matches = matches
            best_dept_name = dept_name

    dept_id = None
    if best_dept_name:
        dept_obj = db.query(Department).filter(Department.nama_dinas == best_dept_name).first()
        if not dept_obj:
            dept_obj = db.query(Department).filter(
                Department.nama_dinas.ilike(f"%{best_dept_name.split(',')[0]}%")
            ).first()
        if dept_obj:
            dept_id = dept_obj.id

    # Fallback jika tidak ada keyword spesifik yang cocok (0 match)
    if not dept_id:
        fallback_dept = db.query(Department).filter(
            Department.nama_dinas == "Dinas Komunikasi dan Informatika"
        ).first()
        if not fallback_dept:
            fallback_dept = db.query(Department).first()
        if fallback_dept:
            dept_id = fallback_dept.id

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
