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
import re
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

KNOWLEDGE_INTENTS = [
    {
        "id": "faq_registrasi_akun",
        "phrases": [
            "bikin akun", "buat akun", "daftar akun", "cara daftar", "cara bikin akun",
            "cara buat akun", "registrasi akun", "cara registrasi", "daftar baru",
            "register", "registrasi", "buka akun", "bikin user", "buat user",
            "daftar warga", "mendaftar akun", "syarat buat akun", "syarat daftar",
            "cara mendaftar", "gagal daftar", "mau daftar"
        ],
        "keywords": ["daftar", "registrasi", "register", "mendaftar"],
        "jawaban": (
            "Panduan Membuat Akun Baru di GovSmart Lamongan:\n\n"
            "1. Buka halaman utama portal GovSmart, lalu klik tautan 'Daftar Baru' (Register).\n"
            "2. Masukkan NIK (Nomor Induk Kependudukan) 16 digit sesuai KTP/KK Anda.\n"
            "3. Masukkan alamat Email yang valid dan aktif untuk keperluan verifikasi/kontak.\n"
            "4. Buat Password yang memenuhi standar keamanan (minimal 8 karakter, wajib kombinasi huruf besar, huruf kecil, angka, dan simbol khusus seperti !@#$%).\n"
            "5. Klik tombol 'Daftar'.\n\n"
            "Setelah registrasi berhasil, akun Anda langsung aktif dan dapat langsung digunakan untuk masuk (login) dengan NIK atau email tersebut."
        ),
        "intent": "faq_registrasi_akun",
        "layanan": "Layanan Pengguna GovSmart",
    },
    {
        "id": "faq_login_akun",
        "phrases": [
            "cara login", "cara masuk", "gagal login", "masuk akun", "tidak bisa login",
            "login gagal", "lupa password", "reset password", "ganti password",
            "keluar akun", "logout", "sesi login", "aturan login", "masuk sistem"
        ],
        "keywords": ["login", "masuk", "logout"],
        "jawaban": (
            "Panduan Masuk (Login) & Manajemen Akun GovSmart:\n\n"
            "1. Pada halaman login, masukkan Email atau NIK (16 digit) Anda pada kolom nama pengguna.\n"
            "2. Masukkan password Anda secara teliti (perhatikan huruf besar/kecil).\n"
            "3. Klik tombol 'Masuk'. Sesi login Anda akan aktif selama 24 jam.\n\n"
            "Catatan Kendala:\n"
            "- Jika muncul pesan salah password/email, periksa kembali pengetikan Anda.\n"
            "- Saat ini fitur reset password otomatis belum tersedia untuk alasan keamanan. Jika Anda lupa password akun, silakan hubungi admin pengelola GovSmart di Dinas Kominfo Kabupaten Lamongan."
        ),
        "intent": "faq_login_akun",
        "layanan": "Layanan Pengguna GovSmart",
    },
    {
        "id": "faq_keamanan_password",
        "phrases": [
            "syarat password", "aturan password", "kriteria password", "format password",
            "kata sandi kuat", "ketentuan password", "password ditolak", "password harus apa"
        ],
        "keywords": ["password", "kata sandi", "sandi"],
        "jawaban": (
            "Ketentuan Standar Keamanan Password GovSmart:\n\n"
            "1. Panjang minimal 8 karakter.\n"
            "2. Mengandung minimal 1 huruf besar (kapital) [A-Z].\n"
            "3. Mengandung minimal 1 huruf kecil [a-z].\n"
            "4. Mengandung minimal 1 angka [0-9].\n"
            "5. Mengandung minimal 1 karakter simbol khusus (contoh: ! @ # $ % ^ & * _ + - =).\n\n"
            "Contoh kombinasi yang valid: 'Lamongan2026!' atau 'WargaCerdas#1'."
        ),
        "intent": "faq_keamanan_password",
        "layanan": "Keamanan Siber GovSmart",
    },
    {
        "id": "panduan_buat_laporan",
        "phrases": [
            "buat laporan", "bikin laporan", "cara melapor", "cara lapor", "kirim laporan",
            "ajukan aduan", "ajukan keluhan", "melapor", "buat aduan", "bikin aduan",
            "laporkan masalah", "cara mengadu", "format laporan", "mengirim laporan", "tulis aduan"
        ],
        "keywords": ["lapor", "aduan", "keluhan", "pengaduan"],
        "jawaban": (
            "Tata Cara Mengajukan Laporan Pengaduan di GovSmart:\n\n"
            "1. Masuk (Login) terlebih dahulu ke akun GovSmart Anda.\n"
            "2. Klik menu 'Buat Laporan' (atau tombol '+ Buat Pengaduan').\n"
            "3. Tuliskan Judul Laporan (5 hingga 100 karakter) yang menggambarkan inti persoalan secara jelas.\n"
            "4. Uraikan Rincian Masalah (20 hingga 2.000 karakter) dengan detail lokasi, patokan alamat, dan kronologi kejadian.\n"
            "5. (Disarankan) Lampirkan Foto Bukti kondisi lapangan (maksimal 5 MB, format JPEG/PNG/WEBP).\n"
            "6. Tentukan titik Koordinat GPS pada peta interaktif.\n"
            "7. Tekan tombol 'Kirim Laporan'.\n\n"
            "Sistem kecerdasan buatan (AI) GovSmart akan otomatis memproses dan merutekan laporan Anda ke dinas terkait."
        ),
        "intent": "panduan_buat_laporan",
        "layanan": "Pengaduan Masyarakat Terpadu",
    },
    {
        "id": "faq_ai_routing",
        "phrases": [
            "dinas tujuan", "pilih dinas", "siapa yang proses", "ai menentukan dinas",
            "salah dinas", "auto routing", "otomatis ke dinas", "pembagian dinas", "sistem ai"
        ],
        "keywords": ["routing", "dinas tujuan", "otomatis", "klasifikasi"],
        "jawaban": (
            "Mekanisme Otomatis Penentuan Dinas (AI Routing GovSmart):\n\n"
            "Di GovSmart, warga tidak perlu bingung memilih dinas tujuan secara manual. Sistem AI cerdas kami bekerja dengan cara:\n"
            "1. Memindai judul dan teks detail laporan Anda menggunakan pencocokan semantik dan kata kunci dari 20 Dinas di Kab. Lamongan.\n"
            "2. Menilai konteks laporan untuk menetapkan dinas berwenang dengan akurasi tertinggi.\n"
            "3. Menentukan tingkat urgensi penanganan (Normal, Penting, atau Darurat).\n"
            "Laporan akan langsung diteruskan ke dasbor kerja dinas bersangkutan untuk ditindaklanjuti."
        ),
        "intent": "faq_ai_routing",
        "layanan": "Sistem AI Routing GovSmart",
    },
    {
        "id": "faq_status_laporan",
        "phrases": [
            "status laporan", "pantau laporan", "cek laporan", "laporan diterima",
            "laporan diproses", "laporan selesai", "laporan ditolak", "riwayat laporan",
            "audit log", "tindak lanjut", "progres laporan", "hasil laporan"
        ],
        "keywords": ["status", "riwayat", "pantau", "progres", "tindak lanjut"],
        "jawaban": (
            "Tahapan Status Pengaduan Anda di GovSmart:\n\n"
            "- Diterima: Laporan berhasil terekam di sistem dan telah masuk ke antrean dinas terkait.\n"
            "- Diproses: Admin Dinas sedang meneliti, memvalidasi, atau menugaskan tim lapangan untuk pengerjaan.\n"
            "- Selesai: Masalah telah ditangani oleh dinas. Petugas biasanya menyertakan catatan penyelesaian dan foto feedback hasil pekerjaan.\n"
            "- Ditolak: Laporan tidak memenuhi kriteria, fiktif, atau di luar kewenangan Pemkab Lamongan (disertai alasan pada catatan petugas).\n\n"
            "Semua perubahan status tercatat secara transparan dalam riwayat audit log laporan Anda."
        ),
        "intent": "faq_status_laporan",
        "layanan": "Transparansi Pelayanan Publik",
    },
    {
        "id": "faq_tingkat_urgensi",
        "phrases": [
            "tingkat urgensi", "urgensi laporan", "laporan darurat", "status darurat",
            "prioritas laporan", "arti darurat", "arti penting", "arti normal"
        ],
        "keywords": ["urgensi", "darurat", "prioritas"],
        "jawaban": (
            "Klasifikasi Tingkat Urgensi Laporan di GovSmart:\n\n"
            "1. Darurat (Emergency): Melibatkan ancaman keselamatan jiwa, bencana alam, kecelakaan parah, kebakaran, atau tanggul jebol. Laporan ini diberi pin merah dan diposisikan paling atas pada antrean dinas.\n"
            "2. Penting: Gangguan fasilitas vital publik yang mendesak untuk ditangani agar tidak meluas (misalnya: jalan amblas, jembatan retak, pipa air utama pecah).\n"
            "3. Normal: Pengaduan umum seputar pelayanan administratif dan fasilitas publik harian."
        ),
        "intent": "faq_tingkat_urgensi",
        "layanan": "Manajemen Tanggap Darurat GovSmart",
    },
    {
        "id": "faq_upload_foto",
        "phrases": [
            "upload foto", "unggah foto", "ukuran foto", "format gambar", "foto bukti",
            "lampiran laporan", "foto ditolak", "bukti dukung", "syarat foto"
        ],
        "keywords": ["foto", "lampiran", "gambar", "unggah", "upload"],
        "jawaban": (
            "Ketentuan Lampiran Foto Bukti di GovSmart:\n\n"
            "- Format berkas: JPEG, JPG, PNG, atau WEBP.\n"
            "- Ukuran maksimal: 5 MB per foto.\n"
            "- Tips: Ambil foto pada siang hari atau pencahayaan cukup yang memperlihatkan titik kerusakan serta objek patokan sekitar (pohon, tiang, bangunan) untuk memudahkan tim peninjau dinas menemukan lokasi."
        ),
        "intent": "faq_upload_foto",
        "layanan": "Dokumentasi Pengaduan",
    },
    {
        "id": "faq_peran_pengguna",
        "phrases": [
            "peran pengguna", "hak akses", "admin dinas", "super admin", "role user",
            "jenis akun", "daftar admin dinas", "siapa super admin", "fungsi admin"
        ],
        "keywords": ["peran", "role", "admin", "warga", "superadmin"],
        "jawaban": (
            "Struktur Peran Pengguna (Roles) di GovSmart:\n\n"
            "1. Warga (Masyarakat/UMKM): Mendaftar secara mandiri, mengajukan pengaduan, memantau tindak lanjut laporan milik sendiri, dan berkonsultasi via chatbot AI.\n"
            "2. Admin Dinas: Petugas perwakilan dari 20 OPD/Dinas di Kabupaten Lamongan. Bertugas memverifikasi laporan masuk, mengubah status penanganan, dan mengunggah foto bukti feedback.\n"
            "3. Super Admin: Administrator pusat Pemkab Lamongan yang mengelola akun admin dinas, data master, serta memantau audit log lintas dinas."
        ),
        "intent": "faq_peran_pengguna",
        "layanan": "Tata Kelola Akses GovSmart",
    },
    {
        "id": "faq_nib_oss",
        "phrases": [
            "bikin nib", "buat nib", "izin usaha", "syarat nib", "izin umkm",
            "oss", "kkpr", "siup", "dpmptsp", "tanda daftar usaha", "izin dagang",
            "usaha mikro", "registrasi oss", "legalitas usaha"
        ],
        "keywords": ["nib", "oss", "umkm", "dpmptsp", "izin usaha", "perizinan", "legalitas"],
        "jawaban": (
            "Panduan Pengurusan NIB (Nomor Induk Berusaha) UMKM di Kabupaten Lamongan:\n\n"
            "1. NIB berfungsi sebagai legalitas usaha tunggal, tanda daftar perusahaan, dan izin edar dasar bagi pelaku usaha mikro & kecil.\n"
            "2. Pendaftaran dilakukan secara daring dan GRATIS melalui portal resmi Online Single Submission di oss.go.id.\n"
            "3. Dokumen Persyaratan:\n"
            "   - KTP (NIK Pemilik Usaha)\n"
            "   - Nomor WhatsApp dan Email aktif\n"
            "   - Data lokasi dan bidang usaha (KBLI 5 digit)\n"
            "4. Layanan Pendampingan Tatap Muka: Jika membutuhkan bimbingan langsung pengisian OSS, Anda dapat mendatangi loket DPMPTSP di Mal Pelayanan Publik (MPP) Kabupaten Lamongan."
        ),
        "intent": "faq_nib_oss",
        "layanan": "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu",
    },
    {
        "id": "faq_adminduk",
        "phrases": [
            "bikin ktp", "buat ktp", "ktp hilang", "ktp rusak", "e-ktp",
            "kartu keluarga", "bikin kk", "akta kelahiran", "akta kematian",
            "surat pindah", "kartu identitas anak", "kia", "disdukcapil", "dukcapil",
            "catatan sipil", "adminduk", "urus kk", "urus ktp"
        ],
        "keywords": ["ktp", "kk", "akta", "kia", "dukcapil", "adminduk", "capil", "kependudukan"],
        "jawaban": (
            "Layanan Administrasi Kependudukan (Disdukcapil Kabupaten Lamongan):\n\n"
            "- KTP-el & KIA: Perekaman biometrik baru, penggantian KTP rusak, atau hilang (membawa surat kehilangan dari Polsek dan fotokopi KK).\n"
            "- Kartu Keluarga (KK): Pembaruan susunan keluarga, penambahan kelahiran anak, atau pemisahan KK.\n"
            "- Akta Kelahiran & Kematian: Penerbitan dokumen akta sipil resmi dengan melampirkan surat pengantar faskes/kelurahan.\n\n"
            "Semua pelayanan kependudukan di Lamongan 100% GRATIS tanpa pungutan biaya. Pengurusan dapat dilakukan langsung di kantor Disdukcapil Lamongan atau melalui loket pelayanan adminduk kantor kecamatan setempat."
        ),
        "intent": "faq_adminduk",
        "layanan": "Dinas Kependudukan dan Pencatatan Sipil",
    },
    {
        "id": "laporan_jalan_rusak",
        "phrases": [
            "jalan rusak", "jalan berlubang", "jembatan rusak", "aspal rusak",
            "bina marga", "jalan amblas", "perbaikan jalan", "jalan retak",
            "gorong-gorong jalan", "aspal terkelupas"
        ],
        "keywords": ["jalan", "lubang", "aspal", "jembatan", "bina marga"],
        "jawaban": (
            "Penanganan Infrastruktur Jalan & Jembatan (Dinas PU Bina Marga Lamongan):\n\n"
            "1. Menangani perbaikan jalan berlubang, pengaspalan jalan poros kabupaten, jembatan rusak, serta longsor tebing jalan.\n"
            "2. Cara Melapor: Buka menu 'Buat Laporan' di GovSmart, ambil foto kerusakan jalan, dan sertakan titik lokasi GPS.\n"
            "3. Laporan yang masuk akan diverifikasi oleh tim Unit Reaksi Cepat (URC) Dinas PU Bina Marga untuk penjadwalan pemeliharaan rutin atau tambal sulam aspal."
        ),
        "intent": "laporan_jalan_rusak",
        "layanan": "Dinas Pekerjaan Umum Bina Marga",
    },
    {
        "id": "laporan_pju",
        "phrases": [
            "lampu jalan", "lampu padam", "pju mati", "lampu mati", "tiang lampu",
            "traffic light", "rambu lalu lintas", "dishub", "lampu penerangan", "penerangan jalan"
        ],
        "keywords": ["lampu", "pju", "dishub", "rambu", "lalin", "traffic"],
        "jawaban": (
            "Pelayanan Penerangan Jalan Umum (PJU) & Lalu Lintas (Dinas Perhubungan Lamongan):\n\n"
            "1. Menangani lampu PJU padam, tiang miring membahayakan, traffic light (lampu merah) error, serta rambu jalan rusak.\n"
            "2. Cara Melapor: Ajukan pengaduan di GovSmart dengan menyertakan nama ruas jalan dan nomor tiang/patokan terdekat.\n"
            "3. Petugas teknis PJU Dishub Lamongan akan melakukan pengecekan sekring/bohlam untuk penggantian komponen di lokasi."
        ),
        "intent": "laporan_pju",
        "layanan": "Dinas Perhubungan",
    },
    {
        "id": "laporan_sampah",
        "phrases": [
            "tumpukan sampah", "sampah liar", "bau sampah", "tps penuh", "tpa",
            "sungai kotor", "pohon tumbang", "dinas lingkungan hidup", "dlh",
            "buang sampah", "kebersihan taman", "limbah lingkungan"
        ],
        "keywords": ["sampah", "kebersihan", "limbah", "dlh", "lingkungan", "tps"],
        "jawaban": (
            "Pengelolaan Sampah & Lingkungan Hidup (Dinas Lingkungan Hidup Lamongan):\n\n"
            "1. Menangani pengaduan tumpukan sampah liar di bahu jalan/saluran air, penumpukan kontainer TPS, serta pemangkasan dahan pohon rawan tumbang di ruang publik.\n"
            "2. Cara Melapor: Kirimkan laporan di GovSmart disertai foto tumpukan sampah dan alamat jelas.\n"
            "3. Tim kebersihan DLH akan mengoordinasikan jadwal pengangkutan armada truk sampah ke lokasi yang dilaporkan."
        ),
        "intent": "laporan_sampah",
        "layanan": "Dinas Lingkungan Hidup",
    },
    {
        "id": "faq_bansos",
        "phrases": [
            "bantuan sosial", "bansos", "pkh", "bpnt", "blt", "daftar bansos",
            "dtks", "keluarga miskin", "dinas sosial", "dinsos", "sembako bantuan", "bantuan warga"
        ],
        "keywords": ["bansos", "pkh", "bpnt", "blt", "dinsos", "dtks", "miskin"],
        "jawaban": (
            "Informasi Bantuan Sosial & Kesejahteraan (Dinas Sosial Lamongan):\n\n"
            "1. Penyaluran bansos (PKH, BPNT, BLT) berbasis pada Data Terpadu Kesejahteraan Sosial (DTKS) Kementerian Sosial.\n"
            "2. Prosedur Usulan Baru: Pendaftaran keluarga prasejahtera dimulai dari musyawarah tingkat desa/kelurahan (Musdes/Muskel) melalui operator SIKS-NG desa.\n"
            "3. Dinas Sosial Kabupaten Lamongan memverifikasi data lapangan dan menyinkronkan usulan ke sistem pusat."
        ),
        "intent": "faq_bansos",
        "layanan": "Dinas Sosial",
    },
    {
        "id": "faq_kesehatan",
        "phrases": [
            "layanan kesehatan", "puskesmas", "rsud soegiri", "bpjs kesehatan",
            "kis", "vaksin", "stunting", "dinas kesehatan", "dinkes",
            "ambulans", "rawat inap", "fasilitas kesehatan"
        ],
        "keywords": ["kesehatan", "puskesmas", "rsud", "dokter", "bpjs", "dinkes", "ambulans", "faskes"],
        "jawaban": (
            "Pelayanan Kesehatan Masyarakat (Dinas Kesehatan & RSUD Lamongan):\n\n"
            "1. Faskes Tingkat Pertama: Pemeriksaan dasar, imunisasi, dan pengobatan rawat jalan dilayani di Puskesmas yang tersebar di seluruh kecamatan Lamongan.\n"
            "2. Layanan Rujukan Lanjutan: RSUD dr. Soegiri Lamongan dan RSUD Ngimbang melayani poliklinik spesialis dan rawat inap.\n"
            "3. Gunakan kepesertaan BPJS Kesehatan / KIS aktif untuk jaminan biaya pelayanan sesuai prosedur rujukan berjenjang."
        ),
        "intent": "faq_kesehatan",
        "layanan": "Dinas Kesehatan",
    },
    {
        "id": "faq_pendidikan",
        "phrases": [
            "dinas pendidikan", "beasiswa", "sekolah rusak", "seragam sekolah",
            "ijazah", "disdik", "bantuan siswa", "program perintis", "dana bos"
        ],
        "keywords": ["sekolah", "pendidikan", "beasiswa", "disdik", "guru", "siswa"],
        "jawaban": (
            "Layanan Pendidikan & Beasiswa (Dinas Pendidikan Lamongan):\n\n"
            "1. Menaungi jenjang PAUD, SD, dan SMP di Kabupaten Lamongan.\n"
            "2. Program Beasiswa Perintis: Program bantuan biaya pendidikan Pemkab Lamongan bagi pelajar dan mahasiswa berprestasi dari keluarga prasejahtera.\n"
            "3. Laporan kerusakan ruang kelas atau sarana pendidikan dapat disampaikan melalui GovSmart untuk pendataan renovasi fisik sekolah."
        ),
        "intent": "faq_pendidikan",
        "layanan": "Dinas Pendidikan",
    },
    {
        "id": "faq_satpolpp",
        "phrases": [
            "satpol pp", "gangguan ketertiban", "razia", "miras", "pkl liar",
            "gelandangan", "pengemis", "kebisingan warga", "penertiban perda"
        ],
        "keywords": ["satpol pp", "satpol", "razia", "tertib", "pengemis", "gepeng"],
        "jawaban": (
            "Ketenteraman & Ketertiban Umum (Satpol PP Lamongan):\n\n"
            "1. Bertugas menegakkan Peraturan Daerah (Perda), penertiban PKL di trotoar yang mengganggu lalu lintas, serta penertiban pengemis/gelandangan di perempatan jalan.\n"
            "2. Aduan ketertiban umum dan kebisingan lingkungan dapat dilaporkan melalui aplikasi GovSmart agar regu patroli Satpol PP segera meninjau ke titik lokasi."
        ),
        "intent": "faq_satpolpp",
        "layanan": "Dinas Satuan Polisi Pamong Praja",
    },
    {
        "id": "wawasan_kebangsaan",
        "phrases": [
            "pancasila", "uud 1945", "nkri", "bhinneka tunggal ika", "wawasan kebangsaan",
            "sumpah pemuda", "proklamasi", "sila pancasila", "nasionalisme", "bela negara"
        ],
        "keywords": ["pancasila", "kebangsaan", "nasionalisme", "uud", "nkri", "bhinneka"],
        "jawaban": (
            "Wawasan Kebangsaan & Nilai Luhur Bangsa Indonesia:\n\n"
            "1. Pancasila: Falsafah dan dasar negara Indonesia yang memuat 5 sila sebagai pedoman moral, hukum, dan tata kehidupan bernegara.\n"
            "2. UUD 1945: Konstitusi tertulis tertinggi yang menjamin hak-hak asasi warga negara dan keadilan sosial.\n"
            "3. NKRI & Bhinneka Tunggal Ika: Semboyan persatuan bangsa yang menegaskan keberagaman suku, agama, dan budaya adalah kekayaan Indonesia.\n\n"
            "GovSmart berkomitmen mewujudkan tata kelola pemerintahan yang berintegritas, transparan, dan berkeadilan bagi seluruh rakyat."
        ),
        "intent": "wawasan_kebangsaan",
        "layanan": "Edukasi Wawasan Kebangsaan",
    },
    {
        "id": "sapaan_dan_bantuan",
        "phrases": [
            "halo", "hai", "assalamu", "selamat pagi", "selamat siang",
            "selamat sore", "selamat malam", "kamu siapa", "bisa apa",
            "menu apa", "bisa bantu apa", "fitur apa"
        ],
        "keywords": ["halo", "hai", "bantuan", "asisten"],
        "jawaban": (
            "Halo! Saya asisten virtual cerdas GovSmart Kabupaten Lamongan. Saya siap membantu Anda seputar:\n\n"
            "1. Pembuatan Akun & Login (klik 'Daftar Baru' di halaman utama)\n"
            "2. Panduan Pengaduan Fasilitas Publik (jalan berlubang, lampu padam, sampah)\n"
            "3. Pengurusan Dokumen Kependudukan (KTP, KK, Akta di Disdukcapil)\n"
            "4. Perizinan Usaha UMKM & Pembuatan NIB melalui OSS\n"
            "5. Informasi Bansos (PKH/DTKS) dan Layanan Faskes/BPJS Kesehatan\n\n"
            "Silakan ketik pertanyaan Anda, saya siap memberikan panduan langkah demi langkah!"
        ),
        "intent": "sapaan",
        "layanan": "Asisten Virtual GovSmart",
    },
]


def generate_builtin_chatbot_response(pertanyaan: str) -> dict:
    q = pertanyaan.lower().strip()

    best_intent = None
    best_score = 0

    for item in KNOWLEDGE_INTENTS:
        score = 0
        # Cocokkan frasa kunci (prioritas tinggi)
        for phrase in item["phrases"]:
            if phrase in q:
                # Frasa lebih panjang diberi bobot lebih besar
                words_count = len(phrase.split())
                score += 8 + (words_count * 4)

        # Cocokkan kata kunci individual
        for kw in item["keywords"]:
            # Cek kecocokan kata utuh
            if re.search(r"\b" + re.escape(kw) + r"\b", q):
                score += 3

        if score > best_score:
            best_score = score
            best_intent = item

    if best_intent and best_score >= 3:
        jawaban = best_intent["jawaban"]
        intent = best_intent["intent"]
        layanan = best_intent["layanan"]
    else:
        jawaban = (
            f"Terima kasih atas pertanyaan Anda seputar '{pertanyaan}'.\n\n"
            "Asisten virtual GovSmart Kabupaten Lamongan dapat membantu Anda dalam beberapa topik berikut:\n"
            "1. Pembuatan Akun & Login (pilih 'Daftar Baru' di halaman login untuk registrasi warga)\n"
            "2. Buat Pengaduan Fasilitas Publik (jalan rusak, lampu jalan padam, tumpukan sampah)\n"
            "3. Dokumen Kependudukan (KTP-el, Kartu Keluarga, Akta di Disdukcapil)\n"
            "4. Izin Usaha & Pembuatan NIB UMKM (melalui OSS di DPMPTSP)\n"
            "5. Bantuan Sosial (PKH/DTKS di Dinas Sosial) & Layanan Kesehatan (Puskesmas/BPJS)\n\n"
            "Silakan ketik pertanyaan yang lebih spesifik seputar topik di atas agar saya dapat memberikan rincian panduan yang tepat."
        )
        intent = "tanya_umum"
        layanan = "Pusat Layanan Informasi Terpadu Pemkab Lamongan"

    return {
        "jawaban": jawaban,
        "intent": intent,
        "mode": "asisten_cerdas",
        "sumber": [
            {
                "no": 1,
                "judul": f"Panduan Resmi {layanan}",
                "konteks": "Pusat Layanan dan Pengaduan Terpadu Pemerintah Kabupaten Lamongan",
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

