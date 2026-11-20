<div align="center">

```
   ██████╗  ██████╗ ██╗   ██╗███████╗███╗   ███╗ █████╗ ██████╗ ████████╗
  ██╔════╝ ██╔═══██╗██║   ██║██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝
  ██║  ███╗██║   ██║██║   ██║███████╗██╔████╔██║███████║██████╔╝   ██║   
  ██║   ██║██║   ██║╚██╗ ██╔╝╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   
  ╚██████╔╝╚██████╔╝ ╚████╔╝ ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   
   ╚═════╝  ╚═════╝   ╚═══╝  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  
```

**Platform E-Governance Cerdas Pemerintah Kabupaten Lamongan**

*AI Smart Routing (20 OPD) · Emergency Classifier · RAG + LLM Multi-Turn Chatbot · GIS Dashboard*

---

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-46%2F46%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](./backend/tests)
[![Chatbot Tests](https://img.shields.io/badge/Chatbot%20Tests-8%2F8%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](./govsmart-chatbot/tests)
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
- [🧪 Menjalankan Unit Test](#-menjalankan-unit-test)
- [📁 Struktur Direktori](#-struktur-direktori)
- [🛠️ Daftar Teknologi](#️-daftar-teknologi)
- [🏛️ Daftar 20 Dinas (OPD) Pemkab Lamongan](#️-daftar-20-dinas-opd-pemkab-lamongan)

---

## 📖 Tentang GovSmart

**GovSmart Lamongan** adalah platform *e-governance* satu pintu berbasis kecerdasan buatan (AI) untuk melayani masyarakat, pelaku UMKM, dan aparatur **Pemerintah Kabupaten Lamongan**. Platform ini mengintegrasikan:

1. **Pelaporan & Pengaduan Publik Berbasis GIS** dengan perutean otomatis berbasis AI ke **20 Dinas (OPD)** dan deteksi tingkat urgensi (`Darurat`, `Penting`, `Normal`).
2. **Asisten Virtual AI Berbasis RAG + LLM** (*Retrieval-Augmented Generation*) yang menjawab pertanyaan layanan perizinan DPMPTSP (NIB/OSS, KKPR, PBG, SLF, AMDAL/SPPL, SIP Nakes), administrasi kependudukan Disdukcapil (KTP-el, KK, KIA, Akta), panduan aplikasi, hingga wawasan kebangsaan dengan **memori percakapan *multi-turn*** dan sitasi dokumen resmi.
3. **Dasbor Manajemen Terpadu (Admin Dinas & Super Admin)** yang responsif penuh di *desktop*, *tablet*, dan *mobile*, lengkap dengan peta sebaran Leaflet interaktif, manajemen akun Admin Dinas & User Warga, audit log transparan, serta ekspor laporan CSV & PDF/HTML.

---

## ✨ Fitur Utama

### 🤖 AI Smart Routing & Emergency Classifier
- Memetakan laporan warga secara otomatis ke **20 Dinas (OPD) Pemkab Lamongan** (toleran terhadap salah ketik / *fuzzy matching*).
- Mengklasifikasikan tingkat urgensi otomatis: `🔴 DARURAT` → `🟡 PENTING` → `🟢 NORMAL`.
- Laporan darurat diprioritaskan di urutan teratas dasbor petugas dinas.

### 💬 Asisten AI GovSmart (RAG + LLM Multi-Turn)
- **Hybrid Retrieval**: Kombinasi *dense vector search* (`intfloat/multilingual-e5-small`, **1.116 chunks** terindeks) + BM25 + *Reciprocal Rank Fusion* (RRF).
- **LLM Generatif + Guardrail Ketat**: Terhubung ke Ollama (`qwen2:1.5b` / `qwen2.5:3b`, `temperature=0.35`) dengan verifikasi relevansi RAG dan perlindungan data pribadi (*PII masking* otomatis untuk NIK & Email).
- **Multi-Turn Memory (hingga 10 giliran)**: Mendukung pertanyaan beruntun pada topik yang sama (misal: *"Berapa lama registrasi KKPR?"* → *"urusnya dimana?"* → *"dokumen yg perlu disiapkan apa aja?"* → *"biayanya berapa?"*).
- **Normalisasi Typo & Dialek Lokal**: Mendukung singkatan percakapan dan kosakata daerah Lamongan/Jawa Timur.

### 📋 Pengaduan Publik Lengkap (Warga)
- Formulir pengaduan dengan judul, deskripsi, pemilihan dinas opsional (atau otomatis oleh AI), tombol **Gunakan Lokasi Saya (GPS)**, serta upload **foto bukti** (JPEG/PNG/WEBP, maks 5 MB).
- **Edit & Batalkan Laporan**: Warga dapat mengedit isi, lokasi, mengganti/menambah foto bukti, atau membatalkan laporan selama status masih `diterima`.
- **Transparansi & Evaluasi**: Warga dapat melihat catatan petugas, membuka **Dokumen/Foto Feedback (PDF/Gambar)** dari dinas, melihat **Riwayat Log (Timeline Status)**, serta memberikan **Rating Kepuasan (1–5 Bintang + Ulasan)** setelah laporan berstatus `selesai`.

### 🗺️ Dasbor Admin Dinas & Super Admin (Responsif Mobile & Desktop)
- **KPI Metrics**: Total pengaduan, urgensi darurat, sedang diproses, persentase selesai, dan rata-rata **Rating Kepuasan Warga**.
- **Peta Sebaran Interaktif (Leaflet)**: Dilengkapi tab khusus *mobile* (`Peta Sebaran` vs `Daftar Pengaduan`), filter berdasarkan dinas, toggle `Hanya Aktif` vs `Semua Status`, legenda warna *collapsible*, serta tombol aksi cepat (`Kelola Status` & `Log`) langsung di popup pin peta.
- **Pembaruan Status & Dokumen Feedback**: Modal interaktif 4 status (`Diterima`, `Diproses`, `Selesai`, `Ditolak`), catatan tindak lanjut, serta upload dokumen bukti pengerjaan (JPEG/PNG/WEBP/PDF maks 5 MB).
- **Filter & Ekspor Laporan**: Filter status (termasuk `Dibatalkan`), filter periode tanggal, pencarian *real-time*, serta **Export CSV** dan **Export PDF/HTML** (lengkap dengan kolom Rating & Ulasan).
- **Manajemen Akun Terpusat (Super Admin)**:
  - **Manajemen Admin Dinas (OPD)**: Tambah akun, filter berdasarkan nama dinas, pencarian NIP/email, edit, nonaktifkan, lihat & aktifkan kembali akun non-aktif, serta hapus permanen.
  - **Manajemen Akun User Warga**: Pencarian nama/NIK/email/telepon, edit profil & reset sandi warga (NIK terkunci), nonaktifkan, lihat & aktifkan kembali akun non-aktif, serta hapus permanen.

### 🔐 Autentikasi, Profil & Keamanan (RBAC + JWT)
- Registrasi warga (NIK 16 digit + email + password kuat), Login dengan tombol **Lihat/Sembunyikan Kata Sandi**, serta fitur **Lupa Kata Sandi (Reset Password Mandiri)** melalui verifikasi kecocokan NIK/NIP dan Email terdaftar.
- **Dropdown Profil Pengguna** di bilah navigasi dengan modal **Lihat & Edit Profil** (ubah nama, email, no. telepon, alamat, dan kata sandi; NIK/NIP dikunci permanen).
- **Pemblokiran Akun Non-aktif**: Akun yang dinonaktifkan (`is_active = False`) otomatis ditolak saat login maupun saat mengakses API (`403 Forbidden`).

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                BROWSER                                  │
│           React 18 + Vite + Leaflet GIS  (localhost:3000)               │
│      Desain Responsif (Desktop & Mobile) · Portal Warga & Admin         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP / REST API (Proxy /api/*)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND — FastAPI (Docker)                        │
│                    Uvicorn ASGI  (localhost:8000)                       │
│   Auth (JWT/RBAC) · Reports (AI Routing/GIS/Export) · Admin · Chat      │
└──────────────┬────────────────────────────────────────┬─────────────────┘
               │ SQLAlchemy ORM                         │ HTTP (X-Internal-Token)
               ▼                                        ▼
┌─────────────────────────────────┐      ┌────────────────────────────────┐
│   DATABASE — MySQL 8.0 (Docker) │      │  CHATBOT RAG SERVICE (Docker)  │
│        (localhost:3307)         │      │        (localhost:8001)        │
│ users · departments · reports   │      │ Hybrid Retriever (E5 + BM25)   │
│ audit_logs · chat_history       │      │ 1.116 Chunks + Multi-Turn      │
└─────────────────────────────────┘      └───────────────┬────────────────┘
                                                         │ OpenAI-compatible API
                                                         ▼
                                         ┌────────────────────────────────┐
                                         │     OLLAMA LLM (Host/Local)    │
                                         │   qwen2:1.5b / qwen2.5:3b      │
                                         └────────────────────────────────┘
```

---

## ⚙️ Prasyarat & Instalasi

| Perangkat Lunak | Versi Minimum | Fungsi |
|----------------|---------------|--------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 4.x | Menjalankan MySQL 8.0, Backend FastAPI, & Chatbot RAG Service |
| [Node.js](https://nodejs.org/) | 18 LTS / 20+ | Menjalankan & mem-*build* Frontend React + Vite |
| [Ollama](https://ollama.com/) *(Opsional — Direkomendasikan)* | Terbaru | Menjalankan model LLM lokal (`qwen2:1.5b` atau `qwen2.5:3b`) untuk jawaban generatif |
| Git | 2.x | Clone repositori |

### Clone Repositori

```bash
git clone https://github.com/username/GovSmart.git
cd GovSmart
```

### Menyiapkan Model LLM Lokal (Opsional untuk Mode Generatif Penuh)

```bash
ollama pull qwen2:1.5b
```

> Jika Ollama belum aktif, layanan `govsmart_chatbot` tetap berjalan normal menggunakan mode *curated intents*, *multi-turn aspect resolver*, dan *extractive RAG*.

---

## 🚀 Menjalankan Aplikasi

### 1. Jalankan Database, Backend, dan Layanan Chatbot RAG via Docker Compose

```bash
docker compose up -d
```

Cek status seluruh kontainer:
```bash
docker compose ps
# Output yang diharapkan:
# govsmart_db       mysql:8.0         Up (healthy)   0.0.0.0:3307->3306/tcp
# govsmart_backend  govsmart-backend  Up             0.0.0.0:8000->8000/tcp
# govsmart_chatbot  govsmart-chatbot  Up             0.0.0.0:8001->8001/tcp
```

### 2. Jalankan Frontend React

Buka terminal baru:

```bash
cd frontend
npm install
npm run dev
```

Atau *build* untuk produksi (disajikan juga oleh backend di `frontend/dist`):
```bash
npm --prefix frontend run build
```

### 🌐 Akses Layanan

| Layanan | URL | Keterangan |
|---------|-----|-----------|
| **🖥️ Portal Web GovSmart** | http://localhost:3000 | Antarmuka Warga, Admin Dinas, & Super Admin |
| **📡 REST API Backend** | http://localhost:8000 | FastAPI Backend |
| **📚 Swagger UI (API Docs)** | http://localhost:8000/docs | Dokumentasi & uji coba API interaktif |
| **🤖 RAG Chatbot Service** | http://localhost:8001/health | Status kesiapan indeks RAG chatbot |
| **❤️ Health Check Backend** | http://localhost:8000/health | Status backend |

---

## 📡 Dokumentasi API

### Akun Bawaan (Auto-Seeded)

Saat pertama kali dijalankan, sistem otomatis membuat:
- **Super Admin**: `superadmin@govsmart.go.id` / Password: `SuperAdmin123!` / NIP: `199001012026011001`
- **Admin Dinas Demo** (2 akun per dinas untuk 20 dinas): `admin.dinas{1..20}.{1..2}@govsmart.go.id` / Password: `AdminDinas123!`

### Ringkasan Endpoint Utama (`/api/v1`)

#### 🔐 Autentikasi (`/api/v1/auth`)
| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `POST` | `/auth/register` | Public | Registrasi akun warga baru (NIK 16 digit, email, password kuat) |
| `POST` | `/auth/login` | Public | Login dengan Email/NIK + password (mendapatkan JWT Token) |
| `POST` | `/auth/reset-password` | Public | Reset kata sandi mandiri dengan verifikasi NIK/NIP + Email |

#### 📋 Laporan Pengaduan (`/api/v1/reports`)
| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `POST` | `/reports/` | Warga | Buat laporan baru (AI Smart Routing & Urgency Classifier) |
| `GET` | `/reports/` | Login | Daftar laporan (filter status, urgensi, dinas, rentang tanggal) |
| `GET` | `/reports/history` | Warga | Ringkasan 5 riwayat laporan terbaru milik warga |
| `GET` | `/reports/{id}` | Login | Detail satu laporan |
| `PUT` | `/reports/{id}` | Warga (pemilik) | Edit laporan saat status masih `diterima` |
| `POST` | `/reports/{id}/cancel` | Warga (pemilik) | Batalkan laporan saat status masih `diterima` |
| `POST` | `/reports/{id}/rating` | Warga (pemilik) | Kirim rating kepuasan (1–5 bintang) & ulasan setelah `selesai` |
| `POST` | `/reports/{id}/upload-foto` | Warga (pemilik) | Upload/ganti foto bukti (JPEG/PNG/WEBP, maks 5 MB) |
| `PATCH` | `/reports/{id}/status` | Admin/Super Admin | Perbarui status laporan & catatan petugas (tercatat di audit log) |
| `POST` | `/reports/{id}/upload-feedback` | Admin/Super Admin | Upload dokumen/foto feedback (JPEG/PNG/WEBP/PDF, maks 5 MB) |
| `GET` | `/reports/notifications/me` | Admin/Super Admin | Notifikasi laporan masuk yang belum selesai |
| `GET` | `/reports/export/csv` | Admin/Super Admin | Ekspor laporan terfilter ke CSV (termasuk rating & ulasan) |
| `GET` | `/reports/export/html` | Admin/Super Admin | Ekspor laporan terfilter ke HTML siap cetak PDF |
| `POST` | `/reports/sync-routing` | Admin/Super Admin | Sinkronisasi ulang AI routing untuk laporan tanpa dinas |

#### 👑 Profil, Admin Dinas, User Warga & Audit (`/api/v1/admin`)
| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `GET` | `/admin/me` | Login | Lihat profil pengguna aktif |
| `PUT` | `/admin/me` | Login | Edit profil pengguna aktif (nama, email, telepon, alamat, sandi; NIK terkunci) |
| `GET` | `/admin/audit-logs/{report_id}` | Pemilik/Admin/Super Admin | Lihat riwayat log (timeline) perubahan status laporan |
| `GET` | `/admin/admin-dinas` | Super Admin | Daftar akun Admin Dinas (mendukung `?include_inactive=true`) |
| `POST` | `/admin/admin-dinas` | Super Admin | Buat akun Admin Dinas baru |
| `PUT` | `/admin/admin-dinas/{id}` | Super Admin | Edit NIP, email, dinas, atau password Admin Dinas |
| `DELETE` | `/admin/admin-dinas/{id}` | Super Admin | Nonaktifkan akun (soft-delete) atau hapus permanen (`?hard=true`) |
| `POST` | `/admin/admin-dinas/{id}/activate` | Super Admin | Aktifkan kembali akun Admin Dinas non-aktif |
| `GET` | `/admin/warga` | Super Admin | Daftar akun User Warga (mendukung `?include_inactive=true`) |
| `PUT` | `/admin/warga/{id}` | Super Admin | Edit data profil atau reset kata sandi akun Warga |
| `DELETE` | `/admin/warga/{id}` | Super Admin | Nonaktifkan akun Warga atau hapus permanen (`?hard=true`) |
| `POST` | `/admin/warga/{id}/activate` | Super Admin | Aktifkan kembali akun Warga non-aktif |

#### 🏛️ Dinas & 💬 AI Chatbot (`/api/v1/departments`, `/api/v1/chat`)
| Method | Endpoint | Akses | Deskripsi |
|--------|----------|-------|-----------|
| `GET` | `/departments/` | Public | Daftar 20 Dinas (OPD) Pemkab Lamongan |
| `POST` | `/chat/` | Login | Kirim pertanyaan (mendukung *multi-turn* hingga 10 giliran) |
| `GET` | `/chat/history` | Login | Lihat riwayat percakapan chatbot milik pengguna |
| `DELETE` | `/chat/history` | Login | Bersihkan riwayat percakapan chatbot milik pengguna |

---

## 🧪 Menjalankan Unit Test

### 1. Backend Test Suite (`46/46 Passed`)
```bash
docker exec govsmart_backend pytest -v
```

### 2. Chatbot RAG Service Test Suite (`8/8 Passed`)
```bash
cd govsmart-chatbot
./venv/bin/pytest -v
```

### 3. Re-Index Dokumen Knowledge Base RAG (Jika Menambah Dokumen Baru)
```bash
cd govsmart-chatbot
./venv/bin/python scripts/extract_docs.py --only .md
./venv/bin/python scripts/chunk_docs.py
./venv/bin/python scripts/build_index.py
docker restart govsmart_chatbot
```

---

## 📁 Struktur Direktori

```
GovSmart-main/
├── 📄 docker-compose.yml              # Orkestrasi MySQL 8.0 + Backend + Chatbot RAG
├── 📄 README.md                       # Dokumentasi utama proyek
├── 📄 DOCUMENTATION.md                # Dokumentasi teknis detail
│
├── 📂 backend/                        # REST API FastAPI + SQLAlchemy
│   ├── 📄 Dockerfile
│   ├── 📄 pyproject.toml
│   ├── 📂 app/
│   │   ├── 📄 main.py                 # Entry point FastAPI & auto-seeder 20 OPD
│   │   ├── 📂 api/endpoints/          # auth, reports, admin, chat, departments
│   │   ├── 📂 core/                   # ai_routing, security, upload, privacy, config
│   │   ├── 📂 models/                 # SQLAlchemy ORM Models
│   │   ├── 📂 schemas/                # Pydantic v2 Schemas
│   │   └── 📂 crud/                   # Operasi database CRUD
│   └── 📂 tests/                      # 46 unit & integration tests (pytest)
│
├── 📂 frontend/                       # SPA React 18 + Vite + Leaflet
│   ├── 📄 package.json
│   ├── 📄 vite.config.js
│   ├── 📂 public/                     # Aset statis termasuk logo-lamongan.png
│   └── 📂 src/
│       ├── 📄 main.jsx
│       ├── 📄 App.jsx                 # Portal Warga, Admin Dinas, Super Admin, & Chatbot
│       └── 📄 index.css               # Design system responsif (Desktop, Tablet, Mobile)
│
└── 📂 govsmart-chatbot/               # Layanan Microservice AI Chatbot (RAG + LLM)
    ├── 📄 Dockerfile
    ├── 📄 service.py                  # FastAPI /ask & /health + PII masking
    ├── 📄 Modelfile                   # Konfigurasi model Ollama (temperature 0.35)
    ├── 📂 knowledge_base/             # Sumber dokumen resmi (MD & PDF)
    ├── 📂 data/                       # Hasil ekstraksi, 1.116 chunks, & embeddings.npy
    ├── 📂 scripts/                    # chatbot.py, retriever.py, typo_corrector.py, indexer
    └── 📂 tests/                      # 8 unit tests service & akurasi RAG
```

---

## 🛠️ Daftar Teknologi

| Layer | Teknologi |
|-------|-----------|
| **Backend** | FastAPI `0.104.1`, Uvicorn, SQLAlchemy `2.0`, Pydantic `v2`, python-jose (JWT), passlib + bcrypt, PyMySQL, httpx, pytest |
| **Frontend** | React `18.2`, Vite `5.4`, React-Leaflet + Leaflet GIS, lucide-react, Vanilla CSS Responsif |
| **AI & RAG Chatbot** | Sentence-Transformers (`intfloat/multilingual-e5-small`), Hybrid Retrieval (Dense + BM25 + RRF), Ollama (`qwen2:1.5b` / `qwen2.5:3b`) |
| **Database & Infra** | MySQL `8.0`, Docker Desktop, Docker Compose V2 |

---

## 🏛️ Daftar 20 Dinas (OPD) Pemkab Lamongan

Sistem *AI Smart Routing* secara otomatis memetakan pengaduan warga ke 20 OPD berikut:

1. Dinas Pendidikan
2. Dinas Kesehatan
3. Dinas Kependudukan dan Pencatatan Sipil (Disdukcapil)
4. Dinas Sosial (Dinsos)
5. Dinas Pemberdayaan Masyarakat dan Desa
6. Dinas Pekerjaan Umum Bina Marga
7. Dinas Pekerjaan Umum Sumber Daya Air (PU SDA)
8. Dinas Perumahan Rakyat, Kawasan Permukiman dan Cipta Karya
9. Dinas Perhubungan (Dishub)
10. Dinas Lingkungan Hidup (DLH)
11. Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu (DPMPTSP)
12. Dinas Tenaga Kerja (Disnaker)
13. Dinas Perikanan
14. Dinas Komunikasi dan Informatika (Diskominfo)
15. Dinas Perpustakaan dan Kearsipan Daerah
16. Dinas Satuan Polisi Pamong Praja (Satpol PP)
17. Dinas Ketahanan Pangan dan Pertanian
18. Dinas Koperasi, Perindustrian, dan Perdagangan
19. Dinas Kebudayaan, Pemuda dan Olahraga dan Pariwisata
20. Dinas Pemberdayaan Perempuan, Perlindungan Anak dan Keluarga Berencana

---

<div align="center">

**Dibuat dengan ❤️ untuk Pemerintah Kabupaten Lamongan**

*GovSmart — Pelayanan Publik Cerdas, Transparan, dan Akuntabel*

</div>
