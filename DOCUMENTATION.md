# Dokumen Fitur & Tools Platform GovSmart

Selamat datang di dokumentasi teknis **GovSmart**, platform e-governance cerdas untuk pelayanan pengaduan masyarakat dan konsultasi perizinan publik Kabupaten Lamongan berbasis **AI Smart Routing & Emergency Classifier**.

---

## 1. 🚀 Fitur-Fitur yang Telah Diimplementasikan & Berjalan

### A. Autentikasi & Keamanan Akses (RBAC & JWT)
* **Registrasi & Login Warga:** Menggunakan NIK (16 digit), Email, dan Password terenkripsi kuat menggunakan `bcrypt`.
* **Super Admin & Admin Dinas Access:** Pembuatan akun Admin Dinas khusus secara terisolasi oleh Super Admin.
* **Role-Based Access Control (RBAC):** Pemisahan hak akses antara `warga`, `admin` (Dinas), dan `super_admin`.
* **JSON Web Token (JWT):** Seluruh endpoint sensitif dilindungi oleh enkripsi token Bearer JWT dengan masa berlaku terkonfigurasi.

### B. Core AI Engine (Smart Routing & Emergency Detection)
* **AI Smart Routing:** Otomatis memetakan isi laporan warga ke salah satu dari **8 Dinas Pemkab Lamongan**:
  1. Dinas Pekerjaan Umum & Penataan Ruang (PU PR)
  2. Dinas Lingkungan Hidup (DLH)
  3. Dinas Kesehatan (Dinkes)
  4. Dinas Perhubungan (Dishub)
  5. Dinas Penanaman Modal & PTSP (DPMPTSP)
  6. Dinas Satuan Polisi Pamong Praja (Satpol PP)
  7. Dinas Pendidikan (Disdik)
  8. Dinas Kependudukan & Pencatatan Sipil (Disdukcapil)
* **Urgency Classifier:** Deteksi otomatis tingkat kedaruratan laporan (`darurat`, `penting`, `normal`) berdasarkan analisa kata kunci bahaya keselamatan/kerusakan fatal.
* **Prioritisasi otomatis:** Laporan ber-urgensi *Darurat* selalu diurutkan paling atas pada feed publik dan dasbor aparatur.

### C. Manajemen Pengaduan Publik & Geokode (CRUD)
* **Form Pengaduan Warga:** Input judul, isi laporan rinci, serta koordinat lokasi (Latitude & Longitude).
* **Transisi Status Laporan:** Admin Dinas dapat memperbarui status laporan dari `menunggu` &rarr; `diproses` &rarr; `selesai` / `ditolak`.
* **Feed Publik:** Tampilan daftar pengaduan warga secara real-time.

### D. Audit Logging System & Akuntabilitas
* **Catatan Audit Otomatis:** Setiap kali admin mengubah status laporan, sistem otomatis mencatat entri ke tabel `audit_logs` (NIP/ID Admin, timestamp, status lama, status baru) untuk menjamin transparansi publik.

### E. AI Chatbot Asisten Perizinan & Layanan Publik
* **Asisten Interaktif:** Chatbot pintar untuk melayani pertanyaan warga terkait perizinan UMKM/NIB, syarat e-KTP, dan panduan dinas.
* **Riwayat Percakapan:** Menyimpan riwayat chat per pengguna (*chat history*).

### F. Pengujian Otomatis (Automatic Unit Testing Suite)
* **11 Unit Test Pytest:** 100% lulus pengujian untuk Auth, CRUD Laporan, AI Smart Routing, Urgency Detection, Status Update, Audit Logs, dan RBAC.

### G. Containerized Infrastructure (Docker & MySQL 8.0)
* **Docker Compose V2:** Orchestration service FastAPI Backend dan Database MySQL 8.0 dengan seeding otomatis 8 Dinas pada startup.

### H. Modern React Web Application (Frontend)
* **Aplikasi Web Single Page (SPA):** Dibangun dengan React.js + Vite dan desain visual modern berbasis **Glassmorphism**.
* **Portal Warga & Feed Publik:** Form pembuatan pengaduan + feed laporan publik.
* **Dasbor Aparatur & Super Admin:** Tabel kelola status, tampilan audit log, dan form pendaftaran admin dinas baru.
* **Floating AI Chatbot Widget:** Widget melayang interaktif di sudut kanan bawah.

---

## 2. 🛠️ Daftar Tools, Package & Kegunaannya

### Backend (Python / FastAPI / MySQL)
| Tools / Package | Versi / Tipe | Kegunaan & Fungsi Utama |
| :--- | :--- | :--- |
| **FastAPI** | Framework Python | Framework backend utama berkinerja tinggi untuk membangun RESTful API asynchronous. |
| **Uvicorn** | Web Server | ASGI Server untuk mengoperasikan FastAPI di environment pengembangan & produksi. |
| **SQLAlchemy** | ORM | Library relasi basis data Python untuk mempermudah query ke MySQL & SQLite. |
| **PyMySQL** & **cryptography** | Driver MySQL | Connector penghubung native antara Python SQLAlchemy dengan database MySQL 8.0. |
| **Pydantic** & **pydantic-settings** | Validation Engine | Pengatur skema tipe data DTO, validasi input API, dan manajemen environment variable `.env`. |
| **python-jose** | Authentication | Pembuat dan penguji token JWT (*JSON Web Tokens*) untuk login pengguna. |
| **passlib** & **bcrypt** (v4.0.1) | Security / Hashing | Enkripsi hash kata sandi pengguna agar aman di basis data. |
| **python-multipart** | Form Parser | Parser data form OAuth2 untuk pemrosesan header login. |
| **pytest**, **pytest-asyncio**, **pytest-cov** | Testing Framework | Framework pengujian unit test dan pengukuran persentase cakupan kode (*code coverage*). |
| **httpx** (v0.27.2) | HTTP Client | Client HTTP asynchronous untuk eksekusi `TestClient` pada pengujian unit test FastAPI. |
| **Docker** & **docker-compose** | Infrastructure | Pembungkus kontainer aplikasi backend dan database MySQL 8.0 agar terisolasi dan mudah di-deploy. |

### Frontend (React / Vite / CSS)
| Tools / Package | Versi / Tipe | Kegunaan & Fungsi Utama |
| :--- | :--- | :--- |
| **React.js** | Library UI (v18) | Framework deklaratif berbasis komponen untuk mengelola antarmuka pengguna SPA. |
| **Vite** | Build Tool | Development server dan bundler modern berbasis ES modules berkecepatan tinggi. |
| **lucide-react** | Icon Set | Pustaka ikon vektor modern untuk komponen UI (Robot, Alert, Building, Shield, Sparkles). |
| **Vanilla CSS (Glassmorphism)** | CSS Custom | Design system visual modern dengan efek kaca buram (*backdrop-filter*), animasi kedaruratan, dan variabel warna dark mode. |

---

## 3. 📖 Petunjuk Pengoperasian Aplikasi

### A. Menjalankan secara Kontainer (Docker Compose - Recommended)
```bash
# Menyalakan Backend & Database MySQL 8.0
sudo docker compose up -d

# Memeriksa Log Kontainer
sudo docker compose logs -f backend
```
> API backend aktif di: `http://localhost:8000` (Dokumentasi Swagger: `http://localhost:8000/docs`)

### B. Menjalankan Frontend Web Portal (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
> Antarmuka Web Portal Warga & Dasbor Admin aktif di: `http://localhost:3000`

### C. Menjalankan Pengujian Otomatis (Unit Test Suite)
```bash
cd backend
poetry run pytest -v
```
