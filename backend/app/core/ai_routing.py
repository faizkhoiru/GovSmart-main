from typing import Tuple, Optional, cast
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

# Zona & Titik Geografis (POI / Koridor) Kabupaten Lamongan untuk Coordinate-Aware Smart Routing
# Format: (nama_zona, lat, long, radius_meter, dinas_terkait)
GEO_ZONES_LAMONGAN = [
    # Kesehatan (RSUD & Faskes Utama)
    ("RSUD dr. Soegiri Lamongan", -7.1204, 112.4119, 300, "Dinas Kesehatan"),
    ("RSUD Ngimbang", -7.3156, 112.2261, 300, "Dinas Kesehatan"),
    ("RSUD Karangkembang Babat", -7.1045, 112.1920, 300, "Dinas Kesehatan"),
    # Perairan / Sumber Daya Air (Sungai, Waduk, Tanggul)
    ("Waduk Gondang Sugio", -7.1995, 112.2750, 700, "Dinas Pekerjaan Umum Sumber Daya Air"),
    ("Tanggul Bengawan Solo Babat", -7.1010, 112.1710, 500, "Dinas Pekerjaan Umum Sumber Daya Air"),
    ("Rawa / Sungai Bengawan Jero", -7.0650, 112.4550, 700, "Dinas Pekerjaan Umum Sumber Daya Air"),
    # Perikanan & Kelautan (Pesisir Utara Lamongan)
    ("Pelabuhan Perikanan & TPI Brondong", -6.8732, 112.2825, 500, "Dinas Perikanan"),
    ("Pelabuhan Kranji Paciran", -6.8685, 112.3710, 450, "Dinas Perikanan"),
    # Pariwisata & Olahraga
    ("Wisata Bahari Lamongan (WBL)", -6.8655, 112.3595, 450, "Dinas Kebudayaan, Pemuda dan Olahraga dan Pariwisata"),
    ("Stadion Surajaya Lamongan", -7.1190, 112.4265, 300, "Dinas Kebudayaan, Pemuda dan Olahraga dan Pariwisata"),
    # Perdagangan & Pasar Utama
    ("Pasar Sidoharjo Lamongan", -7.1165, 112.4169, 250, "Dinas Koperasi, Perindustian, dan Perdagangan"),
    ("Pasar Agrobis Babat", -7.1068, 112.1674, 300, "Dinas Koperasi, Perindustian, dan Perdagangan"),
    # Perizinan & Layanan Publik Pusat
    ("Mal Pelayanan Publik (MPP) Lamongan", -7.1174, 112.4178, 220, "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu"),
    # Ketertiban & Ruang Publik Pusat
    ("Alun-Alun Kabupaten Lamongan", -7.1196, 112.4167, 220, "Dinas Satuan Polisi Pamong Praja"),
    # Terminal & Transportasi
    ("Terminal Lamongan", -7.1168, 112.4045, 280, "Dinas Perhubungan"),
    ("Terminal Babat", -7.1095, 112.1650, 280, "Dinas Perhubungan"),
    # Pendidikan / Kampus (hanya dipakai untuk masalah non-jalan/non-utilitas publik)
    ("PSDKU PENS Lamongan", -7.1155, 112.4280, 220, "Dinas Pendidikan"),
    ("Universitas Islam Lamongan (UNISLA)", -7.1149, 112.4198, 220, "Dinas Pendidikan"),
]

# Kata tempat yang sering menjadi patokan lokasi ("di area kampus", "di depan sekolah", "dekat pasar")
LOCATION_ANCHOR_NOUNS = {
    "kampus", "universitas", "sekolah", "sekolahan", "sd", "smp", "sma", "smk", "paud", "tk", "madrasah",
    "pasar", "toko", "rumah", "perumahan", "desa", "dusun", "kelurahan", "puskesmas", "rumah sakit", "rs",
    "terminal", "pelabuhan", "taman", "stadion", "lapangan", "perpustakaan", "sawah", "kebun",
}

LOCATION_PREP_PATTERN = r"(?:di\s+(?:area|sekitar|depan|dekat|samping|sebelah|belakang|pinggir|sepanjang|lingkungan|wilayah|kawasan|jalan)|area|sekitar|depan|dekat|samping|sebelah|belakang|menuju|arah)"

ROAD_INFRA_TERMS = (
    "jalan", "jalanan", "jalan rusak", "jalan berlubang", "jalan ambruk", "jalan amblas",
    "jalan ambles", "jalan retak", "jalan bolong", "berlubang", "lubang", "aspal", "trotoar", "jembatan",
)
TRAFFIC_PJU_TERMS = (
    "pju", "lampu jalan", "penerangan jalan", "lampu lalu lintas", "traffic light", "rambu", "marka jalan",
)
WATER_DRAIN_TERMS = (
    "banjir", "drainase", "selokan", "got", "irigasi", "tanggul", "longsor", "saluran air", "genangan air",
)
ENV_WASTE_TERMS = (
    "sampah", "tps", "tpa", "limbah", "pohon tumbang", "pencemaran", "bau menyengat",
)


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Hitung jarak (dalam meter) antara dua titik koordinat GPS (WGS84)."""
    import math
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))


def _is_in_lamongan_bounds(lat: float, lon: float) -> bool:
    """Periksa apakah titik koordinat berada dalam cakupan geografis Kabupaten Lamongan."""
    return -7.45 <= lat <= -6.80 and 112.05 <= lon <= 112.55


def analyze_report_ai(
    judul: str,
    isi: str,
    db: Session,
    lat: Optional[float] = None,
    long: Optional[float] = None,
) -> Tuple[Optional[int], str]:
    import re
    from difflib import get_close_matches

    judul_lower = (judul or "").lower()
    isi_lower = (isi or "").lower()
    text_lower = f"{judul_lower} {isi_lower}".strip()

    raw_words = re.findall(r"\b[a-z]+\b", text_lower)
    tokens = set(raw_words)

    # Common typos mapping (termasuk typo kata tempat & infrastruktur seperti 'kammpus', 'jlan', 'rukas')
    typo_aliases = {
        "kebkaran": "kebakaran", "kebakran": "kebakaran", "terbakarrr": "terbakar",
        "kesehtan": "kesehatan", "kesehataan": "kesehatan", "puskes": "puskesmas",
        "sekolahh": "sekolah", "pendidkan": "pendidikan", "beasiswaa": "beasiswa",
        "kammpus": "kampus", "kampuss": "kampus", "kmpus": "kampus",
        "dokterr": "dokter", "jalanann": "jalanan", "berlubng": "berlubang",
        "sampahh": "sampah", "lingkungn": "lingkungan", "banjirr": "banjir",
        "perizinan": "perizinan", "perijinan": "perizinan", "dukcapill": "dukcapil",
        "jlan": "jalan", "jln": "jalan", "jallan": "jalan", "dalan": "jalan",
        "rukas": "rusak", "russak": "rusak", "berlubah": "berlubang", "berlubag": "berlubang",
        "jeglongan": "berlubang", "jembataan": "jembatan", "drainse": "drainase", "selokaan": "selokan",
    }
    tokens.update(typo_aliases[token] for token in list(tokens) if token in typo_aliases)
    normalized_judul = " ".join(typo_aliases.get(w, w) for w in re.findall(r"\b[a-z]+\b", judul_lower))
    normalized_text = " ".join(typo_aliases.get(w, w) for w in raw_words)

    # 1. Determine Urgency (substring match, robust for multi-word)
    urgensi = "normal"
    if any(word in normalized_text or word in text_lower for word in EMERGENCY_KEYWORDS):
        urgensi = "darurat"
    elif any(word in normalized_text or word in text_lower for word in IMPORTANT_KEYWORDS):
        urgensi = "penting"

    # 2. Deteksi kata tempat yang HANYA dipakai sebagai patokan lokasi ("di area kampus", "depan sekolah", dll.)
    location_only_nouns = set()
    for noun in LOCATION_ANCHOR_NOUNS:
        pat = rf"\b{LOCATION_PREP_PATTERN}\s+(?:[a-z]+\s+){{0,1}}{re.escape(noun)}\b"
        if re.search(pat, normalized_text) or re.search(pat, text_lower):
            # Pastikan bukan frasa masalah fasilitas internal seperti "fasilitas kampus", "gedung sekolah", "atap sekolah"
            internal_pat = rf"\b(?:fasilitas|gedung|bangunan|atap|plafon|ruang|pelayanan|layanan|pendaftaran)\s+{re.escape(noun)}\b"
            if not (re.search(internal_pat, normalized_text) or re.search(internal_pat, text_lower)):
                location_only_nouns.add(noun)

    # 3. Weighted Smart Routing berdasarkan kata kunci masalah + judul
    scores: dict[str, float] = {}
    for dept_name, keywords in KEYWORDS_DEPT_MAP.items():
        score = 0.0
        for kw in keywords:
            matched = False
            in_title = False
            if " " in kw:
                if kw in normalized_text or kw in text_lower:
                    matched = True
                    in_title = (kw in normalized_judul or kw in judul_lower)
            else:
                if kw in tokens:
                    matched = True
                    in_title = (kw in set(re.findall(r"\b[a-z]+\b", normalized_judul)))
                elif len(kw) >= 5:
                    for tok in tokens:
                        if abs(len(tok) - len(kw)) <= 1 and get_close_matches(tok, [kw], n=1, cutoff=0.85):
                            matched = True
                            break
            if not matched:
                continue

            if kw in location_only_nouns:
                # Patokan lokasi ("di area kampus", "depan sekolah") diberi bobot rendah agar tidak mengalahkan masalah utama
                score += 0.35
            elif " " in kw:
                # Frasa masalah spesifik (mis. "jalan rusak", "lampu jalan", "fasilitas kampus") berbobot tinggi
                score += 3.0 + (0.75 if in_title else 0.0)
            else:
                score += 1.0 + (0.4 if in_title else 0.0)

        if score > 0:
            scores[dept_name] = score

    # 4. Coordinate-Aware Spatial Routing (memanfaatkan parameter lat & long)
    has_coords = lat is not None and long is not None
    if has_coords:
        try:
            lat_f = float(lat)
            lon_f = float(long)
        except (TypeError, ValueError):
            has_coords = False

    if has_coords:
        is_road_issue = any(t in normalized_text or t in text_lower for t in ROAD_INFRA_TERMS)
        is_traffic_pju_issue = any(t in normalized_text or t in text_lower for t in TRAFFIC_PJU_TERMS)
        is_water_drain_issue = any(t in normalized_text or t in text_lower for t in WATER_DRAIN_TERMS)
        is_env_waste_issue = any(t in normalized_text or t in text_lower for t in ENV_WASTE_TERMS)
        is_public_utility_issue = is_road_issue or is_traffic_pju_issue or is_water_drain_issue or is_env_waste_issue

        # 4a. Spatial Infrastructure Boost untuk masalah jalan/PJU/drainase/sampah di ruang publik Lamongan
        if _is_in_lamongan_bounds(lat_f, lon_f):
            if is_road_issue:
                scores["Dinas Pekerjaan Umum Bina Marga"] = scores.get("Dinas Pekerjaan Umum Bina Marga", 0.0) + 2.0
            if is_traffic_pju_issue:
                scores["Dinas Perhubungan"] = scores.get("Dinas Perhubungan", 0.0) + 2.0
            if is_water_drain_issue:
                scores["Dinas Pekerjaan Umum Sumber Daya Air"] = scores.get("Dinas Pekerjaan Umum Sumber Daya Air", 0.0) + 1.75
            if is_env_waste_issue:
                scores["Dinas Lingkungan Hidup"] = scores.get("Dinas Lingkungan Hidup", 0.0) + 1.5

        # 4b. Pencocokan Zona POI Geografis Kabupaten Lamongan (radius Haversine)
        nearest_zone = None
        nearest_dist = float("inf")
        for zone_name, z_lat, z_lon, z_radius, z_dept in GEO_ZONES_LAMONGAN:
            dist = _haversine_meters(lat_f, lon_f, z_lat, z_lon)
            if dist <= z_radius and dist < nearest_dist:
                nearest_dist = dist
                nearest_zone = (zone_name, z_dept, dist)

        if nearest_zone:
            _, z_dept, _ = nearest_zone
            # Jangan arahkan masalah utilitas jalan/PJU/sampah/banjir ke Dinas Pendidikan/Kesehatan/Perdagangan hanya karena dekat gedung
            if not (is_public_utility_issue and z_dept in (
                "Dinas Pendidikan",
                "Dinas Kesehatan",
                "Dinas Koperasi, Perindustian, dan Perdagangan",
                "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu",
            )):
                scores[z_dept] = scores.get(z_dept, 0.0) + 1.8

        # 4c. Historical Spatial Proximity Tie-Breaker (jika belum ada skor kuat dari teks & zona POI)
        if not scores or max(scores.values()) < 1.0:
            try:
                from app.models.report import Report
                nearby_reports = (
                    db.query(Report)
                    .filter(Report.lat.isnot(None), Report.long.isnot(None), Report.dept_id.isnot(None))
                    .order_by(Report.id.desc())
                    .limit(100)
                    .all()
                )
                for rep in nearby_reports:
                    if rep.lat is None or rep.long is None:
                        continue
                    dist = _haversine_meters(lat_f, lon_f, float(rep.lat), float(rep.long))
                    if dist <= 300.0:
                        dept_hist = db.query(Department).filter(Department.id == rep.dept_id).first()
                        if dept_hist:
                            scores[dept_hist.nama_dinas] = scores.get(dept_hist.nama_dinas, 0.0) + 0.8
                            break
            except Exception:
                pass

    best_dept_name = max(scores.items(), key=lambda kv: kv[1])[0] if scores else None

    dept_id = None
    if best_dept_name:
        dept_obj = db.query(Department).filter(Department.nama_dinas == best_dept_name).first()
        if not dept_obj:
            dept_obj = db.query(Department).filter(
                Department.nama_dinas.ilike(f"%{best_dept_name.split(',')[0]}%")
            ).first()
        if dept_obj:
            dept_id = dept_obj.id

    # Fallback jika tidak ada keyword spesifik maupun zona koordinat yang cocok
    if not dept_id:
        fallback_dept = db.query(Department).filter(
            Department.nama_dinas == "Dinas Komunikasi dan Informatika"
        ).first()
        if not fallback_dept:
            fallback_dept = db.query(Department).first()
        if fallback_dept:
            dept_id = fallback_dept.id

    return cast(Optional[int], dept_id), urgensi

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
