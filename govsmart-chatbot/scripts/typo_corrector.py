"""Modul penanganan typo dan normalisasi bahasa untuk chatbot GovSmart.

Menangani:
1. Singkatan chatting / slang (mis. 'brp' -> 'berapa', 'gmn' -> 'bagaimana', 'syrat' -> 'syarat', 'ijin' -> 'izin').
2. Typo singkatan perizinan/OPD (mis. 'kkp'/'kpr' -> 'kkpr', 'pgb' -> 'pbg', 'ptsp' -> 'dpmptsp').
3. Typo kata kunci domain dengan fuzzy matching (dengan proteksi kata umum agar tidak salah ganti).
"""
import re
import difflib

# 1. Pemetaan kata slang / singkatan chatting / ejaan tidak baku
SLANG_MAP = {
    # Kata tanya & percakapan
    "brp": "berapa",
    "brapa": "berapa",
    "berpa": "berapa",
    "gmn": "bagaimana",
    "gimana": "bagaimana",
    "bgmn": "bagaimana",
    "bagaimna": "bagaimana",
    "bgaiamana": "bagaimana",
    "kpn": "kapan",
    "kpan": "kapan",
    "dmn": "dimana",
    "dimn": "dimana",
    "knp": "kenapa",
    "knpa": "kenapa",
    "mengpa": "mengapa",
    "cra": "cara",
    "cranya": "caranya",
    "carany": "caranya",
    "bs": "bisa",
    "bsa": "bisa",
    "tlg": "tolong",
    "tlng": "tolong",
    "dgn": "dengan",
    "dg": "dengan",
    "utk": "untuk",
    "kpd": "kepada",
    "pd": "pada",
    "sdh": "sudah",
    "udh": "sudah",
    "udah": "sudah",
    "blm": "belum",
    "blom": "belum",
    "tdk": "tidak",
    "gk": "tidak",
    "gak": "tidak",
    "nggak": "tidak",
    "ga": "tidak",
    "sy": "saya",
    "kmi": "kami",
    "km": "kamu",
    "org": "orang",
    "sj": "saja",
    "sja": "saja",
    "ap": "apa",
    "apakh": "apakah",
    "apkah": "apakah",
    "bkin": "bikin",

    # Sapaan & terima kasih
    "haloo": "halo",
    "helo": "halo",
    "hello": "halo",
    "haii": "hai",
    "hallo": "halo",
    "slamat": "selamat",
    "slmt": "selamat",
    "mksih": "terima kasih",
    "makasih": "terima kasih",
    "makasi": "terima kasih",
    "trm": "terima",
    "ksh": "kasih",
    "tengkyu": "terima kasih",
    "thanks": "terima kasih",
    "thx": "terima kasih",

    # Istilah umum layanan & birokrasi
    "syrat": "syarat",
    "sarat": "syarat",
    "srat": "syarat",
    "syaratt": "syarat",
    "persyratan": "persyaratan",
    "persaratn": "persyaratan",
    "ijin": "izin",
    "izn": "izin",
    "ijn": "izin",
    "izinn": "izin",
    "perijinan": "perizinan",
    "periznan": "perizinan",
    "prizinan": "perizinan",
    "prosdur": "prosedur",
    "prosedure": "prosedur",
    "wktu": "waktu",
    "wkt": "waktu",
    "lma": "lama",
    "lmaa": "lama",
    "bya": "biaya",
    "biya": "biaya",
    "byar": "bayar",
    "retribsi": "retribusi",
    "retibusi": "retribusi",
    "retribus": "retribusi",
    "plyanan": "pelayanan",
    "pelaynan": "pelayanan",
    "standart": "standar",
    "stndar": "standar",
    "pmrintah": "pemerintah",
    "pemrintah": "pemerintah",
    "kbupaten": "kabupaten",
    "kabupatn": "kabupaten",
    "lamongn": "lamongan",
    "lmongan": "lamongan",
    "buapti": "bupati",
    "bupti": "bupati",
    "reklm": "reklame",
    "reklam": "reklame",

    # Singkatan perizinan & instansi
    "kkp": "kkpr",
    "kpr": "kkpr",
    "kkppr": "kkpr",
    "kkr": "kkpr",
    "kkprr": "kkpr",
    "pgb": "pbg",
    "pbgg": "pbg",
    "sfl": "slf",
    "slff": "slf",
    "nibb": "nib",
    "nbi": "nib",
    "nb": "nib",
    "os": "oss",
    "osss": "oss",
    "umk": "umkm",
    "ukm": "umkm",
    "umkmm": "umkm",
    "ptsp": "dpmptsp",
    "dpmpstp": "dpmptsp",
    "dpmpsp": "dpmptsp",
    "amdll": "amdal",
    "amdall": "amdal",
    "sppll": "sppl",
    "spl": "sppl",

    # Aplikasi GovSmart
    "govsmrt": "govsmart",
    "gosmart": "govsmart",
    "aplkasi": "aplikasi",
    "apliaksi": "aplikasi",
    "apilkasi": "aplikasi",
    "apliksi": "aplikasi",
    "lapr": "lapor",
    "lpor": "lapor",
    "lapran": "laporan",
    "laporran": "laporan",
    "aduan": "pengaduan",
    "pngaduan": "pengaduan",
    "pengaduaan": "pengaduan",
    "upld": "unggah",
    "upload": "unggah",
    "akn": "akun",
    "dftar": "daftar",
    "daftr": "daftar",
    "dftr": "daftar",
    "lgin": "login",
    "logi": "login",
    "pasword": "password",
    "pssword": "password",
    "katasandi": "kata sandi",
    "ktpp": "ktp",
    "kpt": "ktp",
    "ektp": "ktp",
    "ftur": "fitur",
    "fiturr": "fitur",
    "dasbor": "dashboard",
    "dashbord": "dashboard",

    # Kenegaraan & Sejarah
    "pancasla": "pancasila",
    "pancasilaa": "pancasila",
    "pancasile": "pancasila",
    "pncasila": "pancasila",
    "bndera": "bendera",
    "bndra": "bendera",
    "merahputih": "merah putih",
    "gruda": "garuda",
    "garud": "garuda",
    "bhinneka": "bhinneka",
    "bhineka": "bhinneka",
    "proklmasi": "proklamasi",
    "proklmsi": "proklamasi",
    "uudd": "uud",
    "indonesa": "indonesia",
    "indonsia": "indonesia",
    "presidn": "presiden",
    "prsiden": "presiden",
    "mentri": "menteri",
    "bpupki": "bpupk",
    "ppk": "ppki",
}

# 2. Kata umum bahasa Indonesia (jangan diubah oleh fuzzy match)
COMMON_WORDS = set(
    "yang dan di ke dari untuk dengan pada adalah itu ini apa berapa bagaimana saja atau dalam "
    "akan oleh ada saya bisa dapat apakah siapa kapan mengapa kenapa lama waktu biaya hari syarat "
    "surat nama masa tidak bukan jika kalau boleh mau ingin tahun bulan orang satu dua tiga empat "
    "lima enam tujuh delapan sembilan sepuluh hal jika saat lalu setelah sebelum lebih kurang "
    "baik baru lama cari tahu bantu mohon izin buat cara bikin proses harus wajib".split()
)

# 3. Kosakata resmi domain untuk fuzzy matching (hanya dicocokkan untuk kata panjang >= 4)
DOMAIN_VOCAB = [
    # Perizinan & Pelayanan
    "registrasi", "penerbitan", "persetujuan", "kesesuaian", "kegiatan", "pemanfaatan",
    "ruang", "bangunan", "gedung", "fungsi", "lingkungan", "usaha", "berusaha",
    "dinas", "penanaman", "modal", "terpadu", "standar", "pelayanan", "mekanisme",
    "prosedur", "jangka", "waktu", "biaya", "retribusi", "persyaratan", "syarat",
    "reklame", "kesehatan", "hewan", "praktek", "kelayakan", "perizinan", "pemerintah",
    "kabupaten", "lamongan", "bupati", "peraturan", "keputusan",

    # Singkatan resmi
    "kkpr", "pbg", "slf", "nib", "oss", "umkm", "umku", "amdal", "sppl", "pkplh", "skkl",
    "dpmptsp", "opd", "rtr", "ktp", "uud", "nkri", "bpupk", "ppki",

    # Aplikasi
    "govsmart", "aplikasi", "akun", "lapor", "laporan", "pengaduan", "unggah", "bukti",
    "password", "sandi", "fitur", "dasbor", "masuk", "daftar", "verifikasi",

    # Kenegaraan
    "pancasila", "bendera", "lambang", "garuda", "bhinneka", "proklamasi", "merdeka",
    "kemerdekaan", "kebangsaan", "konstitusi", "presiden", "menteri", "gubernur",
    "pahlawan", "bangsa", "negara", "indonesia"
]

_VOCAB_SET = set(DOMAIN_VOCAB)


def koreksi_kata(kata: str) -> str:
    """Koreksi satu kata jika merupakan slang atau memiliki typo."""
    k_lower = kata.lower()

    # 1. Cek kamus slang/typo langsung
    if k_lower in SLANG_MAP:
        return SLANG_MAP[k_lower]

    # 2. Jika kata termasuk kata umum atau kosakata resmi domain, jangan diubah
    if k_lower in COMMON_WORDS or k_lower in _VOCAB_SET:
        return kata

    # 3. Fuzzy matching hanya untuk kata yang cukup panjang (>= 4 karakter)
    if len(k_lower) >= 4 and k_lower.isalpha():
        matches = difflib.get_close_matches(k_lower, DOMAIN_VOCAB, n=1, cutoff=0.80)
        if matches:
            return matches[0]

    return kata


def koreksi_teks(teks: str) -> str:
    """Koreksi seluruh teks pertanyaan dari typo dan singkatan percakapan."""
    if not teks or not isinstance(teks, str):
        return teks

    def _sub(match):
        return koreksi_kata(match.group(0))

    return re.sub(r"\b[A-Za-z0-9_-]+\b", _sub, teks)
