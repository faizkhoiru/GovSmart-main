"""Modul penanganan typo dan normalisasi bahasa untuk chatbot GovSmart.

Menangani:
1. Singkatan chatting / slang (mis. 'brp' -> 'berapa', 'gmn' -> 'bagaimana', 'syrat' -> 'syarat', 'ijin' -> 'izin').
2. Typo singkatan perizinan/OPD (mis. 'kkp'/'kpr' -> 'kkpr', 'pgb' -> 'pbg', 'ptsp' -> 'dpmptsp').
3. Typo kata kunci domain dengan fuzzy matching berproteksi kamus kata umum Bahasa Indonesia.
"""
import re
import difflib

SLANG_MAP = {
    # Kata tanya & percakapan sehari-hari
    "brp": "berapa",
    "brapa": "berapa",
    "berpa": "berapa",
    "gmn": "bagaimana",
    "gmna": "bagaimana",
    "gmana": "bagaimana",
    "gimana": "bagaimana",
    "bgmn": "bagaimana",
    "bagaimna": "bagaimana",
    "bgaiamana": "bagaimana",
    "bgaimana": "bagaimana",
    "kpn": "kapan",
    "kpan": "kapan",
    "dmn": "dimana",
    "dimn": "dimana",
    "kmn": "kemana",
    "kmna": "kemana",
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
    "untk": "untuk",
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
    "enggak": "tidak",
    "sy": "saya",
    "aku": "saya",
    "gue": "saya",
    "gw": "saya",
    "kmi": "kami",
    "km": "kamu",
    "lu": "kamu",
    "lo": "kamu",
    "org": "orang",
    "sj": "saja",
    "sja": "saja",
    "aja": "saja",
    "aj": "saja",
    "ap": "apa",
    "apaa": "apa",
    "apakh": "apakah",
    "apkah": "apakah",
    "bkin": "bikin",
    "pake": "pakai",
    "pkai": "pakai",
    "gunain": "gunakan",
    "make": "pakai",
    "yg": "yang",
    "klo": "kalau",
    "kalo": "kalau",
    "kl": "kalau",
    "krn": "karena",
    "karna": "karena",
    "tp": "tetapi",
    "tpi": "tetapi",
    "jd": "jadi",
    "jdi": "jadi",
    "dr": "dari",
    "dri": "dari",
    "sm": "sama",
    "sma": "sama",
    "lg": "lagi",
    "lgi": "lagi",
    "hrs": "harus",
    "haruss": "harus",
    "mhn": "mohon",
    "tau": "tahu",
    "cowo": "cowok",
    "cewe": "cewek",

    # Sapaan & terima kasih
    "haloo": "halo",
    "helo": "halo",
    "hello": "halo",
    "haii": "hai",
    "hallo": "halo",
    "slamat": "selamat",
    "slmt": "selamat",
    "mksih": "terima kasih",
    "mksh": "terima kasih",
    "makasih": "terima kasih",
    "makasi": "terima kasih",
    "trimakasih": "terima kasih",
    "trims": "terima kasih",
    "trm": "terima",
    "ksh": "kasih",
    "tengkyu": "terima kasih",
    "thanks": "terima kasih",
    "thx": "terima kasih",
    "tq": "terima kasih",

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
    "retribsi": "retribusi",
    "retibusi": "retribusi",
    "retribus": "retribusi",
    "plyanan": "pelayanan",
    "pelaynan": "pelayanan",
    "layann": "layanan",
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
    "kkppr": "kkpr",
    "kkr": "kkpr",
    "kkprr": "kkpr",
    "pgb": "pbg",
    "pbgg": "pbg",
    "sfl": "slf",
    "slff": "slf",
    "nibb": "nib",
    "nbi": "nib",
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

    # Aplikasi GovSmart
    "govsmrt": "govsmart",
    "gosmart": "govsmart",
    "aplkasi": "aplikasi",
    "apliaksi": "aplikasi",
    "apilkasi": "aplikasi",
    "apliksi": "aplikasi",
    "lapr": "lapor",
    "lpor": "lapor",
    "mlapor": "melapor",
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
    "smpah": "sampah",

    # Kenegaraan & Sejarah
    "pancasla": "pancasila",
    "pancsila": "pancasila",
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
    "negraa": "negara",
    "presidn": "presiden",
    "prsiden": "presiden",
    "mentri": "menteri",
    "bpupki": "bpupk",
}

COMMON_WORDS = set(
    "yang dan di ke dari untuk dengan pada adalah itu ini apa berapa bagaimana saja atau dalam "
    "akan oleh ada saya bisa dapat apakah siapa kapan mengapa kenapa lama waktu biaya hari syarat "
    "surat nama masa tidak bukan jika kalau boleh mau ingin tahun bulan orang satu dua tiga empat "
    "lima enam tujuh delapan sembilan sepuluh hal saat lalu setelah sebelum lebih kurang "
    "baik baru cari tahu bantu mohon izin buat cara bikin proses harus wajib "
    "pakai gunakan menggunakan hapus menghapus edit mengedit ubah mengubah batal batalkan membatalkan "
    "bantuan layanan aturan data angka jangan keselamatan mereka penataan penertiban pengaman "
    "pupuk tanda terdekat ulang uang bangun bayar membayar gratis daftar mendaftar terdaftar "
    "lapor melapor melaporkan pelaporan dilaporkan mengadukan unggah diunggah berubah berusia alokasi "
    "jalan lampu sampah banjir sekolah dokter rumah sakit masuk keluar lupa ganti tolong bingung "
    "aduh cowok cewek laki perempuan manusia robot terima kasih coba lihat pantau status riwayat "
    "foto gambar lokasi peta dinas camat desa lurah warga masyarakat warung toko dagang akta "
    "nikah lahir mati padam pindah kartu keluarga anak miskin sosial dana anggaran pajak tanah "
    "lahan sawah ikan nelayan kerja lowongan hilang rusak parah darurat penting normal "
    "kirim dikirim diterima diproses selesai ditolak dibatalkan "
    "persatuan kesatuan perbedaan kedudukan kedaulatan demokrasi identitas wawasan kebangsaan "
    "sumpah pemuda pembelaan bela sila pertama kedua ketiga keempat kelima perbaikan memperbaiki "
    "menghubungi menanyakan dibacakan menerapkan keamanan tercemar tergenang tersumbat menumpuk "
    "operasional pungutan kopdes bumdes koperasi paspor imigrasi stnk bpkb skck samsat npwp bpn "
    "kemenkumham prakerja cpns pppk subsidi pinjaman kredit kuliner wisata kereta jadwal surabaya "
    "sukodadi ketenagakerjaan jamsostek notaris pendirian vaksin halal".split()
)

DOMAIN_VOCAB = [
    # Perizinan & Pelayanan
    "registrasi", "penerbitan", "persetujuan", "kesesuaian", "kegiatan", "pemanfaatan",
    "ruang", "bangunan", "gedung", "fungsi", "lingkungan", "usaha", "berusaha",
    "dinas", "penanaman", "modal", "terpadu", "standar", "pelayanan", "mekanisme",
    "prosedur", "jangka", "waktu", "biaya", "retribusi", "persyaratan", "syarat",
    "reklame", "kesehatan", "hewan", "praktek", "kelayakan", "perizinan", "pemerintah",
    "kabupaten", "lamongan", "bupati", "peraturan", "keputusan", "kependudukan",
    "pencatatan", "sipil", "dukcapil", "disdukcapil", "perhubungan", "dishub",
    "pendidikan", "disdik", "puskesmas", "beasiswa",

    # Singkatan resmi
    "kkpr", "pbg", "slf", "nib", "oss", "umkm", "umku", "amdal", "sppl", "pkplh", "skkl",
    "dpmptsp", "opd", "rtr", "ktp", "uud", "nkri", "bpupk", "ppki", "dtks", "bansos",

    # Aplikasi
    "govsmart", "aplikasi", "akun", "lapor", "laporan", "pengaduan", "unggah", "bukti",
    "password", "sandi", "fitur", "dasbor", "dashboard", "masuk", "daftar", "verifikasi",
    "koordinat", "urgensi",

    # Kenegaraan
    "pancasila", "bendera", "lambang", "garuda", "bhinneka", "proklamasi", "merdeka",
    "kemerdekaan", "kebangsaan", "konstitusi", "presiden", "menteri", "gubernur",
    "pahlawan", "bangsa", "negara", "indonesia", "nasionalisme"
]

_VOCAB_SET = set(DOMAIN_VOCAB)


def koreksi_kata(kata: str) -> str:
    """Koreksi satu kata jika merupakan slang atau memiliki typo pada istilah domain."""
    k_lower = kata.lower()

    if k_lower in SLANG_MAP:
        return SLANG_MAP[k_lower]

    if k_lower in COMMON_WORDS or k_lower in _VOCAB_SET:
        return kata

    if len(k_lower) >= 6 and k_lower.isalpha():
        kandidat = [v for v in DOMAIN_VOCAB if v[0] == k_lower[0] and abs(len(v) - len(k_lower)) <= 2]
        matches = difflib.get_close_matches(k_lower, kandidat, n=1, cutoff=0.86)
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
