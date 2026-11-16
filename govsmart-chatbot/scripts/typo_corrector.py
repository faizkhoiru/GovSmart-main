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

    # === TAMBAHAN 200+ VARIASI TYPO, SLANG, DAN BAHASA CHAT HARIAN ===
    # Kata ganti & Panggilan santai / netizen (termasuk typo)
    "gw": "saya", "gwe": "saya", "gue": "saya", "gua": "saya", "guwa": "saya", "gwa": "saya",
    "w": "saya", "ane": "saya", "kulo": "saya", "dalem": "saya", "awak": "saya",
    "km": "kamu", "kmu": "kamu", "kmw": "kamu", "kamuu": "kamu", "kamuuh": "kamu",
    "lu": "kamu", "loo": "kamu", "luh": "kamu", "elu": "kamu", "eluu": "kamu",
    "ente": "kamu", "sampeyan": "kamu", "panjenengan": "kamu", "koen": "kamu",
    "qta": "kita", "kt": "kita", "ktaa": "kita", "kitaa": "kita",
    "mimin": "admin", "miminn": "admin", "minn": "admin", "minnn": "admin",
    "adminn": "admin", "admn": "admin", "admnn": "admin", "minss": "admin",
    "kakk": "kak", "kakkk": "kak", "kaka": "kak", "kaak": "kak", "kakakk": "kak", "kka": "kak",
    "broo": "kak", "bray": "kak", "bre": "kak", "cuy": "kak", "cuyy": "kak", "coy": "kak", "coyy": "kak",
    "gan": "kak", "gann": "kak", "agann": "kak", "agan2": "kak", "sob": "kak", "sobb": "kak", "sobat": "kak",
    "pakmin": "admin", "bumin": "admin", "mbakmin": "admin", "masmin": "admin",

    # Meminta Bantuan / Bertanya / Permohonan (termasuk typo & slang)
    "bntu": "bantu", "bntuu": "bantu", "bantui": "bantu", "bntuin": "bantu",
    "bantuin": "bantu", "bantuiin": "bantu", "bntuinn": "bantu", "bantuu": "bantu",
    "bantuann": "bantuan", "bntuan": "bantuan", "bntuannya": "bantuan", "bntuanx": "bantuan",
    "bntunya": "bantuan", "bntuanmu": "bantuan", "bantuannya": "bantuan",
    "tlong": "tolong", "tlongg": "tolong", "tlongin": "tolong", "tlng": "tolong",
    "tlngg": "tolong", "tlngin": "tolong", "tolongg": "tolong", "tolongin": "tolong",
    "tolonginlah": "tolong", "bantulah": "bantu", "tlonglah": "tolong",
    "tnya": "tanya", "tny": "tanya", "tnyak": "tanya", "tnyakan": "tanya",
    "tnykan": "tanya", "tanyain": "tanya", "tanykan": "tanya", "tnyaa": "tanya",
    "nnya": "tanya", "nny": "tanya", "nnyak": "tanya", "nanyaa": "tanya",
    "nanyain": "tanya", "nyanya": "tanya", "bertnya": "bertanya", "brtanya": "bertanya",
    "mw": "mau", "mox": "mau", "mauu": "mau", "mauw": "mau", "mew": "mau", "moo": "mau",
    "pgn": "ingin", "pngen": "ingin", "pgen": "ingin", "pengin": "ingin",
    "pngin": "ingin", "pengenn": "ingin", "pengn": "ingin",
    "knsl": "konsultasi", "konsul": "konsultasi", "konsultasii": "konsultasi",
    "inpo": "info", "inponya": "info", "inpoh": "info", "infokan": "info",
    "infokn": "info", "inffo": "info", "informasii": "informasi",
    "bimbing": "panduan", "bimbingan": "panduan", "bmbing": "panduan",
    "pnduan": "panduan", "panduann": "panduan", "tutoriall": "panduan", "tuturial": "panduan",
    "help": "bantu", "helpp": "bantu", "tulung": "tolong", "ngewangi": "bantu",

    # Status Laporan, Cek, Pantau, Pengaduan (termasuk typo)
    "lapr": "lapor", "lpor": "lapor", "lporkn": "lapor", "laporkn": "lapor",
    "laporin": "lapor", "ngelapor": "lapor", "ngelaporin": "lapor", "laporann": "laporan",
    "laporran": "laporan", "lpordan": "laporan", "laporane": "laporan",
    "aduan": "pengaduan", "aduanx": "pengaduan", "adukan": "pengaduan", "aduin": "pengaduan",
    "ngadu": "pengaduan", "ngaduin": "pengaduan", "pngaduan": "pengaduan",
    "pengduan": "pengaduan", "pengaduann": "pengaduan",
    "kluhan": "keluhan", "kluhn": "keluhan", "keluhann": "keluhan", "ngeluh": "keluhan",
    "ck": "cek", "ckk": "cek", "cekk": "cek", "ceking": "cek", "ngecek": "cek", "ngecekk": "cek",
    "liat": "lihat", "lhat": "lihat", "liatt": "lihat", "ngeliat": "lihat",
    "diliat": "dilihat", "delok": "lihat", "ndelok": "lihat",
    "pantow": "pantau", "panto": "pantau", "pantaw": "pantau", "pantauu": "pantau",
    "mantau": "pantau", "memantau": "pantau",
    "apdet": "update", "updet": "update", "updt": "update", "updetan": "update", "terupdate": "update",
    "stts": "status", "statuss": "status", "statuse": "status", "sttus": "status",
    "riwayt": "riwayat", "riwayatt": "riwayat", "histori": "riwayat", "history": "riwayat",
    "nyari": "cari", "nyri": "cari", "cr": "cari", "carii": "cari", "mencarii": "cari",
    "dpt": "dapat", "dpat": "dapat", "dapetin": "dapat", "ngedapetin": "dapat", "dptin": "dapat", "dptnya": "dapat",

    # Kata Kerja & Modalitas Aksi (termasuk typo)
    "bisaa": "bisa", "bsak": "bisa", "biza": "bisa", "bsia": "bisa", "bise": "bisa", "bisakahh": "bisakah",
    "bolehk": "boleh", "bleh": "boleh", "blh": "boleh", "bolehh": "boleh", "bole": "boleh", "bolehkahh": "bolehkah",
    "mbikin": "bikin", "bikinin": "bikin", "bkinin": "bikin", "bkinn": "bikin", "bwt": "buat", "buatt": "buat",
    "pke": "pakai", "pkei": "pakai", "pkai": "pakai", "pakee": "pakai", "gunakn": "gunakan", "gnakan": "gunakan", "makai": "pakai",
    "editan": "ubah", "ngedit": "ubah", "ngubah": "ubah", "ngerubah": "ubah", "rubah": "ubah", "ngerevisi": "ubah",
    "btal": "batal", "btlin": "batal", "batalin": "batal", "ngebatalin": "batal", "batalinn": "batal",
    "hps": "hapus", "hapuss": "hapus", "ngapus": "hapus", "ngapusin": "hapus", "hapusin": "hapus",
    "krm": "kirim", "krim": "kirim", "kirimm": "kirim", "ngirim": "kirim", "ngirimin": "kirim", "kirimin": "kirim",
    "unggahh": "unggah", "ngunggah": "unggah", "uplod": "unggah", "aplod": "unggah", "uploadan": "unggah", "aplodan": "unggah",
    "fto": "foto", "poto": "foto", "potret": "foto", "gambarr": "foto", "gmbr": "foto", "gmbrnya": "foto",
    "lokasi": "lokasi", "loksi": "lokasi", "lks": "lokasi", "lokasine": "lokasi", "titik": "lokasi",
    "koordinatt": "koordinat", "kordinat": "koordinat", "kordinatt": "koordinat",
    "dftr": "daftar", "daftrr": "daftar", "daftarin": "daftar", "daftarkan": "daftar", "ndaftar": "daftar",
    "pendaftaran": "daftar", "pendftaran": "daftar", "daptar": "daftar",
    "regis": "registrasi", "regist": "registrasi", "regstrasi": "registrasi", "regristrasi": "registrasi", "regris": "registrasi",
    "msuk": "masuk", "masukk": "masuk", "loginnya": "login", "loginn": "login",
    "kluar": "keluar", "klwr": "keluar", "logoutt": "logout",
    "psswrd": "password", "pasword": "password", "passwrd": "password", "pass": "password", "pwd": "password",
    "ngerti": "paham", "ngertii": "paham", "ngarti": "paham", "mudeng": "paham", "mdeng": "paham", "faham": "paham", "pham": "paham",
    "bener": "benar", "bnr": "benar", "bnar": "benar", "beneran": "benar", "betull": "benar", "btul": "benar", "btl": "benar",
    "salahh": "salah", "keliru": "salah", "slh": "salah", "eror": "rusak", "errorr": "rusak", "erorr": "rusak", "rusakk": "rusak",

    # Sapaan & Obrolan Kasual (termasuk typo)
    "aslm": "halo", "ass": "halo", "assalam": "halo", "assalamualaikum": "halo",
    "assalamuallaikum": "halo", "assalamu'alaikum": "halo", "askum": "halo", "mikum": "halo", "samlikum": "halo",
    "selmt": "selamat", "met": "selamat",
    "pgi": "pagi", "pagii": "pagi", "pagiii": "pagi",
    "siank": "siang", "sianggg": "siang",
    "sree": "sore", "soreee": "sore",
    "malemm": "malam", "malem": "malam",
    "halloo": "halo", "heloo": "halo", "helloo": "halo", "haiii": "hai", "hei": "hai", "heii": "hai", "hy": "hai", "hii": "hai",
    "kbr": "kabar", "kbar": "kabar", "kbrnya": "kabar", "kabarn": "kabar", "kabare": "kabar", "kabaran": "kabar",
    "piye": "bagaimana", "pripun": "bagaimana", "pripune": "bagaimana", "waras": "sehat",
    "makasihh": "terima kasih", "mksihh": "terima kasih", "makacih": "terima kasih", "tengkiu": "terima kasih",
    "maturnuwun": "terima kasih", "suwun": "terima kasih", "kesuwun": "terima kasih",
    "sama2": "sama-sama", "sm2": "sama-sama", "samasama": "sama-sama",
    "dadah": "sampai jumpa", "byebye": "sampai jumpa", "bye-bye": "sampai jumpa", "sampaijumpaa": "sampai jumpa",
    "pinteer": "pintar", "cerdass": "pintar", "kerenn": "pintar", "mantapp": "mantap", "mantul": "mantap", "mantabb": "mantap",
    "lucuu": "lucu", "wkwkk": "lucu", "wkwkwk": "lucu", "xixixi": "lucu", "hehehe": "lucu", "hahaha": "lucu",

    # Kata Hubung, Waktu, & Partikel Percakapan (termasuk typo)
    "jgn": "jangan", "jgan": "jangan", "jngan": "jangan", "jngn": "jangan", "jngnn": "jangan",
    "kgk": "tidak", "kagak": "tidak", "kaga": "tidak", "ngga": "tidak", "ngak": "tidak", "ngk": "tidak",
    "emg": "memang", "emang": "memang", "mmg": "memang", "emng": "memang",
    "mksud": "maksud", "maksd": "maksud", "mksd": "maksud", "mksudnya": "maksud", "maksut": "maksud",
    "skrg": "sekarang", "skrang": "sekarang", "skr": "sekarang", "skrng": "sekarang", "now": "sekarang",
    "bsk": "besok", "bsok": "besok", "kmarin": "kemarin", "kmrin": "kemarin",
    "cpt": "cepat", "cepet": "cepat", "cpet": "cepat", "sgera": "segera", "sgra": "segera",
    "bnyk": "banyak", "byk": "banyak", "dkit": "dikit", "sdkit": "sedikit",
    "krg": "kurang", "kurg": "kurang", "lbih": "lebih", "lbh": "lebih",
    "bgt": "banget", "bgtt": "banget", "bngat": "banget", "bgtu": "begitu", "gtu": "begitu", "gini": "begini", "gni": "begini",
    "knp": "kenapa", "knpa": "kenapa", "knpaa": "kenapa", "napa": "kenapa", "ngapa": "kenapa",
    "ngapain": "kenapa", "ngapn": "kenapa", "knape": "kenapa",
    "dlu": "dulu", "duluu": "dulu", "tdi": "tadi", "tadii": "tadi",
    "trs": "terus", "trus": "terus", "trss": "terus", "lgsg": "langsung", "lngsng": "langsung",
    "smpai": "sampai", "sampe": "sampai", "smpe": "sampai",
    "pdhl": "padahal", "pdahal": "padahal", "mskipun": "meskipun",
    "mgkn": "mungkin", "mngkin": "mungkin", "plg": "paling", "pling": "paling",
    "sprti": "seperti", "spt": "seperti", "cntoh": "contoh", "cntohnya": "contoh",

    # Istilah Layanan Publik & Pemkab Lamongan (termasuk typo)
    "lamongann": "lamongan", "lamongane": "lamongan", "lmg": "lamongan", "pemkab": "pemerintah",
    "dpmptspnya": "dpmptsp", "dpmp-tsp": "dpmptsp", "ptsp": "dpmptsp", "dpm": "dpmptsp",
    "osss": "oss", "oss-rba": "oss", "osba": "oss",
    "nibb": "nib", "nibbnya": "nib", "nyb": "nib", "nbi": "nib",
    "kkprr": "kkpr", "kkppr": "kkpr", "kkp": "kkpr", "kkr": "kkpr",
    "pbgg": "pbg", "pgb": "pbg", "imb": "pbg",
    "slff": "slf", "sfl": "slf",
    "ektp": "ktp", "e-ktp": "ktp", "ktpel": "ktp", "ktp-el": "ktp", "el-ktp": "ktp",
    "kartukeluarga": "kartu keluarga", "kartu-keluarga": "kartu keluarga",
    "kartuanak": "kia", "kartu-identitas-anak": "kia",
    "aktalahir": "akta kelahiran", "aktamati": "akta kematian", "akte": "akta",
    "dukcapill": "dukcapil", "disduk": "dukcapil", "dispendukcapil": "dukcapil", "capill": "dukcapil",
    "dishubb": "dishub", "pjumati": "pju mati", "lampujalan": "lampu jalan", "lampumerah": "lampu merah",
    "binamarga": "bina marga", "bnamarga": "bina marga", "jalanrusak": "jalan rusak", "jalanberlubang": "jalan rusak",
    "lingkunganhidup": "lingkungan hidup", "sampahliar": "sampah", "tumpukansampah": "sampah",
    "puskemas": "puskesmas", "puskes": "puskesmas", "puskesms": "puskesmas",
    "sogiri": "soegiri", "sugiri": "soegiri",
    "satpolpp": "satpol pp", "satpol-pp": "satpol pp", "satpol": "satpol pp",
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
