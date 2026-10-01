<div align="center">

```
   ██████╗  ██████╗ ██╗   ██╗███████╗███╗   ███╗ █████╗ ██████╗ ████████╗
  ██╔════╝ ██╔═══██╗██║   ██║██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝
  ██║  ███╗██║   ██║██║   ██║███████╗██╔████╔██║███████║██████╔╝   ██║   
  ██║   ██║██║   ██║╚██╗ ██╔╝╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   
  ╚██████╔╝╚██████╔╝ ╚████╔╝ ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   
   ╚═════╝  ╚═════╝   ╚═══╝  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  
```

**Platform E-Governance Cerdas Pemkab Lamongan**

*AI Smart Routing · Emergency Classifier · Chatbot Perizinan*

---

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Pytest](https://img.shields.io/badge/Tests-15%2F15%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](./backend/tests)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## 📋 Daftar Isi

- [📖 Tentang GovSmart](#-tentang-govsmart)
- [✨ Fitur Utama](#-fitur-utama)
- [🏗️ Arsitektur Sistem](#️-arsitektur-sistem)
- [⚙️ Prasyarat & Instalasi](#️-prasyarat--instalasi)
- [🚀 Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [📡 Dokumentasi API](#-dokumentasi-api)
- [🔑 Panduan Penggunaan](#-panduan-penggunaan)
- [🧪 Menjalankan Unit Test](#-menjalankan-unit-test)
- [📁 Struktur Direktori](#-struktur-direktori)
- [🛠️ Daftar Teknologi](#️-daftar-teknologi)

---

## 📖 Tentang GovSmart

**GovSmart** adalah platform *e-governance* berbasis kecerdasan buatan yang dirancang untuk melayani warga dan aparatur **Pemerintah Kabupaten Lamongan**. Sistem ini menggabungkan pengaduan publik berbasis geolokasi, perutean laporan otomatis berbasis AI ke 8 Dinas terkait, dan asisten chatbot layanan perizinan — semuanya dalam satu platform terintegrasi.

> 💡 **Dirancang untuk:** Mempercepat respons pemerintah terhadap pengaduan warga dan memudahkan akses informasi layanan publik secara digital.

---

## ✨ Fitur Utama

### 🤖 AI Smart Routing & Emergency Classifier
- Otomatis memetakan laporan warga ke **8 Dinas Pemkab Lamongan** berdasarkan analisis kata kunci
- Mendeteksi tingkat urgensi laporan: `🔴 DARURAT` → `🟡 PENTING` → `🟢 NORMAL`
- Laporan darurat selalu diprioritaskan ke urutan paling atas pada feed publik dan dasbor aparatur

### 🔐 Autentikasi & Keamanan (RBAC + JWT)
- Registrasi warga menggunakan NIK 16 digit
- **Role-Based Access Control** dengan 3 level peran:

  | Peran | Akses |
  |-------|-------|
  | `warga` | Buat & lihat laporan sendiri, gunakan chatbot |
  | `admin` (Dinas) | Kelola status laporan dinas terkait, lihat audit log |
  | `super_admin` | Buat akun Admin Dinas, akses penuh semua laporan |

- Password wajib kuat: huruf besar + kecil + angka + simbol

### 📋 Manajemen Pengaduan (CRUD + GIS)
- Form laporan dengan judul, deskripsi rinci, dan koordinat **GPS (Lat/Long)**
- Upload **foto bukti kerusakan** (JPEG/PNG/WEBP, maks 5 MB)
- Transisi status laporan: `diterima` → `diproses` → `selesai` / `ditolak`

### 📝 Audit Logging & Transparansi
- Setiap perubahan status laporan otomatis tercatat di tabel `audit_logs`
- Rekam jejak lengkap: ID Admin, timestamp, status lama → status baru

### 💬 AI Chatbot Asisten Perizinan
- Melayani pertanyaan seputar **NIB/UMKM**, **e-KTP**, **Kartu Keluarga**, dan **panduan pengaduan**
- Riwayat percakapan tersimpan per pengguna

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                         BROWSER                             │
│           React 18 + Vite  (localhost:3000)                 │
│        Glassmorphism UI · AI Chatbot Widget                 │
└─────────────────────┬───────────────────────────────────────┘
                      │  HTTP / REST API (Proxy /api/*)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND — FastAPI                           │
│               Uvicorn ASGI  (localhost:8000)                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │   Auth   │  │ Reports  │  │  Admin   │  │  Chatbot  │  │
│  │   JWT    │  │ AI Route │  │  RBAC    │  │  Perizinan│  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                       │                                     │
│              SQLAlchemy ORM                                 │
└───────────────────────┼─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              DATABASE — MySQL 8.0 (Docker)                  │
│   users · departments · reports · audit_logs · chat_history │
└─────────────────────────────────────────────────────────────┘
```

**Tabel Database:**

| Tabel | Keterangan |
|-------|-----------|
| `users` | Data warga & aparatur (NIK/NIP, email, role, password hash) |
| `departments` | 8 Dinas Pemkab Lamongan (auto-seeded) |
| `reports` | Laporan pengaduan + geolokasi + foto bukti |
| `audit_logs` | Rekam jejak perubahan status laporan |
| `chat_history` | Riwayat percakapan chatbot per pengguna |

---

## ⚙️ Prasyarat & Instalasi

### Prasyarat

Pastikan perangkat lunak berikut sudah terpasang di komputer Anda:

| Perangkat Lunak | Versi Minimum | Fungsi |
|----------------|---------------|--------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 4.x | Menjalankan backend & database |
| [Node.js](https://nodejs.org/) | 18 LTS (atau 20/22) | Menjalankan frontend React |
| Git | 2.x | Clone repositori |

> **💡 Mac Intel (x86_64)?** Unduh Docker Desktop melalui link langsung:  
> `https://desktop.docker.com/mac/main/amd64/Docker.dmg`

### Clone Repositori

```bash
git clone https://github.com/username/GovSmart.git
cd GovSmart
```

### Konfigurasi Environment (Opsional)

Backend sudah memiliki nilai *default* yang berfungsi langsung tanpa konfigurasi tambahan. Namun untuk kustomisasi, salin dan edit file `.env`:

```bash
cp backend/.env.example backend/.env
```

```env
# backend/.env
SECRET_KEY=supersecretkeygovsmart2026!
ACCESS_TOKEN_EXPIRE_MINUTES=1440

MYSQL_USER=govsmart_user
MYSQL_PASSWORD=govsmart_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=govsmart
```

---

## 🚀 Menjalankan Aplikasi

### Metode 1: Docker Compose — Rekomendasi ⭐

Cara paling mudah: satu perintah untuk menyalakan **backend FastAPI + MySQL 8.0** secara bersamaan. Database, tabel, dan data awal dibuat **otomatis**.

```bash
# Di folder root proyek (GovSmart/)
docker compose up -d
```

Cek status kontainer:
```bash
docker compose ps
# Output yang diharapkan:
# govsmart_db       mysql:8.0          Up (healthy)   0.0.0.0:3307->3306/tcp
# govsmart_backend  govsmart-backend   Up             0.0.0.0:8000->8000/tcp
```

Melihat log realtime backend:
```bash
docker compose logs -f backend
```

### Metode 2: Menjalankan Frontend React

Buka terminal **baru** (terpisah dari terminal Docker), lalu jalankan:

```bash
cd GovSmart/frontend

# Install dependensi (hanya perlu dijalankan sekali)
npm install

# Jalankan development server
npm run dev
```

---

### 🌐 Akses Aplikasi

| Layanan | URL | Keterangan |
|---------|-----|-----------|
| **🖥️ Portal Web Warga** | http://localhost:3000 | Antarmuka utama (React + Glassmorphism) |
| **⚙️ Dasbor Admin & Super Admin** | http://localhost:3000 | Login dengan akun admin |
| **📡 REST API Backend** | http://localhost:8000 | FastAPI backend |
| **📚 Swagger UI (API Docs)** | http://localhost:8000/docs | Dokumentasi & uji coba API interaktif |
| **📘 ReDoc (API Docs)** | http://localhost:8000/redoc | Dokumentasi API alternatif |
| **❤️ Health Check** | http://localhost:8000/health | Status backend |

---

## 📡 Dokumentasi API

### Akun Bawaan (Auto-Seeded)

Saat pertama kali dijalankan, sistem otomatis membuat akun Super Admin:

| Field | Nilai |
|-------|-------|
| **Email** | `superadmin@govsmart.go.id` |
| **Password** | `SuperAdmin123!` |
| **NIP** | `199001012026011001` |
| **Role** | `super_admin` |

### Daftar Endpoint API

#### 🔐 Autentikasi (`/api/v1/auth`)

| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `POST` | `/auth/register` | Public | Registrasi warga baru (NIK, email, password) |
| `POST` | `/auth/login` | Public | Login, mendapatkan JWT Bearer Token |

**Aturan Password:**
- Minimal 8 karakter
- Harus mengandung: huruf besar (A–Z), huruf kecil (a–z), angka (0–9), simbol (`!@#$%^&*`)

#### 📋 Laporan Pengaduan (`/api/v1/reports`)

| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `POST` | `/reports/` | Warga | Buat laporan baru (AI routing otomatis) |
| `GET` | `/reports/` | Warga/Admin | Daftar laporan (filter status, urgensi, dinas) |
| `GET` | `/reports/{id}` | Warga/Admin | Detail satu laporan |
| `PATCH` | `/reports/{id}/status` | Admin/Super Admin | Update status laporan |
| `POST` | `/reports/{id}/upload-foto` | Warga (pemilik) | Upload foto bukti (JPEG/PNG/WEBP, maks 5 MB) |

**Status Laporan yang Valid:** `diterima` · `diproses` · `selesai` · `ditolak`

**Tingkat Urgensi (diisi AI):** `🔴 darurat` · `🟡 penting` · `🟢 normal`

#### 👑 Manajemen Admin (`/api/v1/admin`)

| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `GET` | `/admin/me` | Semua (login) | Lihat profil pengguna aktif |
| `POST` | `/admin/admin-dinas` | Super Admin | Buat akun Admin Dinas baru |
| `GET` | `/admin/audit-logs/{report_id}` | Admin/Super Admin | Lihat rekam jejak perubahan laporan |

#### 🏛️ Dinas (`/api/v1/departments`)

| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `GET` | `/departments/` | Public | Daftar 8 Dinas Pemkab Lamongan |

#### 💬 AI Chatbot (`/api/v1/chat`)

| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `POST` | `/chat/` | Warga (login) | Kirim pertanyaan ke chatbot |
| `GET` | `/chat/history` | Warga (login) | Lihat riwayat percakapan |

---

## 🔑 Panduan Penggunaan

### Alur Lengkap sebagai Warga

```
1. Registrasi Akun Warga
   POST /api/v1/auth/register
   Body: { "nik_or_nip": "3524...", "email": "...", "password": "Kuat@99!" }

2. Login & Dapatkan Token
   POST /api/v1/auth/login
   Form: username=email&password=...
   → Simpan access_token dari response

3. Buat Laporan Pengaduan
   POST /api/v1/reports/
   Header: Authorization: Bearer <token>
   Body: { "judul": "Jalan berlubang...", "isi_laporan": "...", "lat": -7.1, "long": 112.1 }
   → AI otomatis menentukan dept_id & urgensi

4. Upload Foto Bukti (Opsional)
   POST /api/v1/reports/{id}/upload-foto
   Header: Authorization: Bearer <token>
   Form: foto=<file.jpg> (JPEG/PNG/WEBP, maks 5 MB)

5. Tanya Chatbot Perizinan
   POST /api/v1/chat/
   Header: Authorization: Bearer <token>
   Body: { "prompt": "Bagaimana cara membuat NIB untuk UMKM?" }
```

### Alur sebagai Admin Dinas

```
1. Login dengan akun admin yang dibuat Super Admin
   → Gunakan NIP sebagai username

2. Lihat Laporan Masuk ke Dinas Anda
   GET /api/v1/reports/?dept_id=<id_dinas>

3. Update Status Laporan
   PATCH /api/v1/reports/{id}/status
   Body: { "status": "diproses" }
   → Audit log otomatis tercatat

4. Lihat Rekam Jejak Laporan
   GET /api/v1/admin/audit-logs/{report_id}
```

### Cara Menggunakan Swagger UI

1. Buka **http://localhost:8000/docs** di browser
2. Klik tombol **Authorize 🔓** (pojok kanan atas)
3. Masukkan `username: superadmin@govsmart.go.id` dan `password: SuperAdmin123!`
4. Klik **Authorize** → klik **Close**
5. Semua endpoint kini bisa diuji langsung via tombol **Try it out**

---

## 🧪 Menjalankan Unit Test

Test suite menggunakan **pytest** dengan database SQLite *in-memory* (tanpa perlu MySQL aktif).

```bash
# Jalankan semua test via Docker (recommended)
docker exec govsmart_backend poetry run pytest -v

# Atau dengan coverage report
docker exec govsmart_backend poetry run pytest -v --cov=app --cov-report=term-missing
```

**Hasil yang diharapkan: 15/15 PASSED ✅**

```
tests/test_admin.py::test_super_admin_create_admin_dinas     PASSED
tests/test_admin.py::test_warga_cannot_create_admin_dinas    PASSED
tests/test_admin.py::test_get_departments_list               PASSED
tests/test_auth.py::test_register_warga_success              PASSED
tests/test_auth.py::test_register_duplicate_email            PASSED
tests/test_auth.py::test_login_success                       PASSED
tests/test_auth.py::test_login_invalid_password              PASSED
tests/test_auth.py::test_register_weak_password_rejected     PASSED  ← Baru
tests/test_auth.py::test_register_strong_password_accepted   PASSED  ← Baru
tests/test_chat.py::test_ask_chatbot_umkm_licensing          PASSED
tests/test_chat.py::test_get_chat_history                    PASSED
tests/test_reports.py::test_submit_report_ai_routing...      PASSED
tests/test_reports.py::test_admin_update_status_and_audit    PASSED
tests/test_reports.py::test_upload_foto_success              PASSED  ← Baru
tests/test_reports.py::test_upload_foto_invalid_mime         PASSED  ← Baru

======================== 15 passed in 7.24s ========================
```

---

## 📁 Struktur Direktori

```
GovSmart/
├── 📄 docker-compose.yml         # Orkestrasi Backend + MySQL 8.0
├── 📄 DOCUMENTATION.md           # Dokumentasi fitur lengkap
│
├── 📂 backend/
│   ├── 📄 Dockerfile
│   ├── 📄 pyproject.toml         # Dependensi Python (Poetry)
│   ├── 📂 app/
│   │   ├── 📄 main.py            # Entry point FastAPI & auto-seeder
│   │   ├── 📄 database.py        # Koneksi SQLAlchemy
│   │   ├── 📂 api/
│   │   │   ├── 📄 api.py         # Router utama
│   │   │   ├── 📄 deps.py        # Dependency injection (JWT, RBAC)
│   │   │   └── 📂 endpoints/
│   │   │       ├── 📄 auth.py    # Register & Login
│   │   │       ├── 📄 reports.py # CRUD Laporan + Upload Foto
│   │   │       ├── 📄 admin.py   # Manajemen Admin & Audit
│   │   │       ├── 📄 chat.py    # AI Chatbot
│   │   │       └── 📄 departments.py
│   │   ├── 📂 core/
│   │   │   ├── 📄 ai_routing.py  # AI Smart Routing & Urgency Classifier
│   │   │   ├── 📄 upload.py      # Validasi upload foto (MIME, 5MB limit)
│   │   │   ├── 📄 security.py    # JWT & bcrypt
│   │   │   └── 📄 config.py      # Konfigurasi environment
│   │   ├── 📂 models/            # SQLAlchemy ORM Models
│   │   ├── 📂 schemas/           # Pydantic Request/Response Schemas
│   │   └── 📂 crud/              # Logika database (CRUD operations)
│   └── 📂 tests/
│       ├── 📄 conftest.py        # Fixtures pytest
│       ├── 📄 test_auth.py       # Test autentikasi & password
│       ├── 📄 test_reports.py    # Test laporan & upload foto
│       ├── 📄 test_admin.py      # Test RBAC admin
│       └── 📄 test_chat.py       # Test chatbot
│
└── 📂 frontend/
    ├── 📄 package.json           # Dependensi Node.js
    ├── 📄 vite.config.js         # Konfigurasi Vite + proxy API
    └── 📂 src/
        ├── 📄 main.jsx           # Entry point React
        ├── 📄 App.jsx            # Komponen utama (SPA)
        └── 📄 index.css          # Design system Glassmorphism
```

---

## 🛠️ Daftar Teknologi

### Backend

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| **FastAPI** | 0.104.1 | Framework REST API async berkinerja tinggi |
| **Uvicorn** | 0.24.0 | ASGI web server |
| **SQLAlchemy** | 2.0.23 | ORM untuk koneksi MySQL |
| **Pydantic v2** | 2.5.0 | Validasi skema data & environment |
| **python-jose** | 3.3.0 | Generate & validasi JWT |
| **passlib + bcrypt** | 4.0.1 | Enkripsi hash password |
| **PyMySQL** | 1.1.0 | Driver koneksi MySQL |
| **pytest** | 7.4.3 | Framework unit testing |

### Frontend

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| **React.js** | 18.2.0 | Library UI berbasis komponen |
| **Vite** | 5.0.8 | Build tool & dev server modern |
| **lucide-react** | 0.294.0 | Ikon vektor modern |
| **Vanilla CSS** | — | Design system Glassmorphism custom |

### Infrastruktur

| Teknologi | Fungsi |
|-----------|--------|
| **Docker Desktop** | Containerization aplikasi |
| **Docker Compose V2** | Orkestrasi multi-container |
| **MySQL 8.0** | Database relasional utama |

---

## 🏛️ 8 Dinas Pemkab Lamongan

GovSmart secara otomatis memetakan laporan ke dinas berikut:

| # | Nama Dinas | Kata Kunci Laporan |
|---|-----------|-------------------|
| 1 | Dinas Pekerjaan Umum & Penataan Ruang | jalan, jembatan, drainase, infrastruktur |
| 2 | Dinas Lingkungan Hidup | sampah, limbah, banjir, polusi, taman |
| 3 | Dinas Kesehatan | puskesmas, ambulans, dokter, demam |
| 4 | Dinas Perhubungan | lampu lalu lintas, macet, parkir, rambu |
| 5 | Dinas Penanaman Modal & PTSP | izin, UMKM, NIB, investasi |
| 6 | Dinas Satuan Polisi Pamong Praja | PKL, ketertiban, kebisingan |
| 7 | Dinas Pendidikan | sekolah, guru, beasiswa, ijazah |
| 8 | Dinas Kependudukan & Pencatatan Sipil | KTP, KK, akta, pindahan |

---

<div align="center">

**Dibuat dengan ❤️ untuk Pemkab Lamongan**

*GovSmart — Pelayanan Publik Cerdas, Transparan, dan Akuntabel*

</div>
