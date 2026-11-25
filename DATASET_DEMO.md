# Panduan Dataset Demo & Uji Coba — GovSmart Kabupaten Lamongan

Dokumen ini berisi **akun siap pakai**, **data laporan demo berkoordinat GPS Kabupaten Lamongan**, serta **contoh skenario uji coba** yang bisa langsung dibagikan kepada teman atau penguji untuk mencoba seluruh fitur GovSmart.

---

## 1. Akun Siap Pakai (Langsung Login)

### A. Super Admin (Akses Penuh 20 OPD + Manajemen Admin & Warga)
| Email | NIP | Password | Role |
|---|---|---|---|
| `superadmin@govsmart.go.id` | `199001012026011001` | `SuperAdmin123!` | `super_admin` |

### B. Akun Warga Demo (6 Akun — Password Sama: `WargaLamongan123!`)
| Nama Lengkap | Email | NIK (16 Digit) | Password | Wilayah |
|---|---|---|---|---|
| Budi Santoso | `budi.santoso@warga.lamongan.id` | `3524011205950001` | `WargaLamongan123!` | Kec. Lamongan |
| Siti Aminah | `siti.aminah@warga.lamongan.id` | `3524022408980002` | `WargaLamongan123!` | Kec. Babat |
| Ahmad Fauzi | `ahmad.fauzi@warga.lamongan.id` | `3524031503920003` | `WargaLamongan123!` | Kec. Paciran |
| Dewi Lestari | `dewi.lestari@warga.lamongan.id` | `3524040711960004` | `WargaLamongan123!` | Kec. Sukodadi |
| Hendra Wijaya | `hendra.wijaya@warga.lamongan.id` | `3524051906940005` | `WargaLamongan123!` | Kec. Deket |
| Rina Kartika | `rina.kartika@warga.lamongan.id` | `3524062809990006` | `WargaLamongan123!` | Kec. Brondong |

### C. Contoh Akun Admin Dinas (Password Semua Admin Dinas: `AdminDinas123!`)
| Dinas (OPD) | Email | Password |
|---|---|---|
| Dinas Pendidikan | `admin.dinas1.1@govsmart.go.id` | `AdminDinas123!` |
| Dinas Kesehatan | `admin.dinas2.1@govsmart.go.id` | `AdminDinas123!` |
| Disdukcapil | `admin.dinas3.1@govsmart.go.id` | `AdminDinas123!` |
| Dinas Sosial | `admin.dinas4.1@govsmart.go.id` | `AdminDinas123!` |
| Dinas PU Bina Marga | `admin.dinas6.1@govsmart.go.id` | `AdminDinas123!` |
| Dinas PU Sumber Daya Air | `admin.dinas7.1@govsmart.go.id` | `AdminDinas123!` |
| Dinas Perhubungan (Dishub) | `admin.dinas9.1@govsmart.go.id` | `AdminDinas123!` |
| Dinas Lingkungan Hidup (DLH) | `admin.dinas10.1@govsmart.go.id` | `AdminDinas123!` |
| DPMPTSP | `admin.dinas11.1@govsmart.go.id` | `AdminDinas123!` |
| Satpol PP | `admin.dinas16.1@govsmart.go.id` | `AdminDinas123!` |

*(Tersedia lengkap untuk seluruh 20 OPD dengan pola `admin.dinas{1..20}.{1..2}@govsmart.go.id`)*

---

## 2. Dataset Laporan Demo yang Sudah Terisi (18 Laporan Berkoordinat GPS)

Database telah diisi **18 laporan pengaduan realistis** yang tersebar di Kecamatan Lamongan, Babat, Paciran, Sukodadi, Deket, Tikung, Brondong, Ngimbang, Sugio, Kedungpring, Karanggeneng, Turi, dan Modo dengan variasi:
- **Status lengkap**: `Diterima`, `Diproses`, `Selesai` (lengkap dengan **Rating 4–5 Bintang & Ulasan Warga**), `Ditolak`, dan `Dibatalkan`.
- **Urgensi lengkap**: `Darurat` (tanggul jebol/banjir, pohon tumbang, jalan ambruk), `Penting`, dan `Normal`.
- **Audit Log Timeline**: Setiap laporan sudah memiliki riwayat perubahan status sehingga tombol **Riwayat Log** dan **Peta Sebaran Leaflet** langsung hidup.

---

## 3. Contoh Input untuk Dicoba Teman Anda

### A. Uji Coba Form Pengaduan (AI Smart Routing & Typo Tolerance)
Coba kirim pengaduan **tanpa memilih dinas (biarkan "Otomatis oleh AI")**:
1. **Uji Darurat + Jalan Rusak (Typo)**:
   - Judul: `Jlan rukas ambruk di depan pasar`
   - Isi: `Aspal jalan poros berlubang parah dan ambruk setelah hujan, sangat membahayakan pengendara motor.`
   - Hasil yang diharapkan: **Dinas PU Bina Marga** · Urgensi **DARURAT**.
2. **Uji Lampu PJU Mati**:
   - Judul: `Lampu jalan PJU mati di perempatan desa`
   - Isi: `Lampu penerangan jalan umum padam total sejak tiga malam lalu sehingga jalanan gelap gulita.`
   - Hasil yang diharapkan: **Dinas Perhubungan** · Urgensi **DARURAT / PENTING**.
3. **Uji Validasi Notifikasi Ramah**:
   - Coba isi Judul hanya 2 huruf (`ab`) atau Isi kurang dari 20 huruf -> perhatikan notifikasi toast kini menampilkan pesan Bahasa Indonesia yang jelas (bukan error code mentah).

### B. Uji Coba Asisten AI Chatbot (Single-Turn, Multi-Turn, Dialek, & Guardrail)
1. **Uji Daftar Topik**:
   - `daftar pertanyaan yg bisa kutanyain?`
2. **Uji Multi-Turn Beruntun (5+ Giliran)**:
   - Giliran 1: `Berapa lama proses registrasi KKPR?`
   - Giliran 2: `urusnya dimana?`
   - Giliran 3: `dokumen yg perlu disiapkan apa aja?`
   - Giliran 4: `biayanya berapa? apakah gratis?`
   - Giliran 5: `gimana langkah-langkah pengurusannya?`
3. **Uji Dialek / Bahasa Santai Lamongan**:
   - `dalan depan rumahku jeglongan parah lapor kemana?`
   - `halo min, syarat bikin e-ktp baru apa aja ya?`
4. **Uji Guardrail Anti-Halusinasi (Di Luar Dokumen Resmi)**:
   - `resep nasi goreng lamongan paling enak`
   - `cara bikin paspor di imigrasi`

---

## 4. Cara Mengisi Ulang Dataset Demo (Jika Database Baru / Di-reset)

Jalankan perintah berikut dari root folder proyek (aman dijalankan berulang kali karena *idempotent*):

```bash
docker exec govsmart_backend python scripts/seed_demo_dataset.py
```

