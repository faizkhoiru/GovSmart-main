#!/usr/bin/env python3
"""
Seeder Dataset Demo GovSmart Kabupaten Lamongan (Idempotent).

Menambahkan:
- 6 akun Warga demo realistis (password: WargaLamongan123!)
- 18 laporan pengaduan publik berkoordinat GPS asli wilayah Kabupaten Lamongan
  lintas berbagai OPD, status (diterima, diproses, selesai, ditolak, dibatalkan),
  urgensi (darurat, penting, normal), catatan petugas, audit log, & rating kepuasan warga.

Cara menjalankan:
    docker exec govsmart_backend python scripts/seed_demo_dataset.py
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.report import Report
from app.models.audit import AuditLog
from app.core.security import get_password_hash
from app.core.ai_routing import analyze_report_ai


DEMO_WARGA = [
    {
        "nik_or_nip": "3524011205950001",
        "email": "budi.santoso@warga.lamongan.id",
        "nama_lengkap": "Budi Santoso",
        "no_telepon": "081234560001",
        "alamat": "Jl. Lamongrejo No. 18, Kel. Sidokumpul, Kec. Lamongan",
    },
    {
        "nik_or_nip": "3524022408980002",
        "email": "siti.aminah@warga.lamongan.id",
        "nama_lengkap": "Siti Aminah",
        "no_telepon": "081234560002",
        "alamat": "Jl. Raya Babat No. 45, Kec. Babat, Kab. Lamongan",
    },
    {
        "nik_or_nip": "3524031503920003",
        "email": "ahmad.fauzi@warga.lamongan.id",
        "nama_lengkap": "Ahmad Fauzi",
        "no_telepon": "081234560003",
        "alamat": "Ds. Paciran RT 03 RW 02, Kec. Paciran, Kab. Lamongan",
    },
    {
        "nik_or_nip": "3524040711960004",
        "email": "dewi.lestari@warga.lamongan.id",
        "nama_lengkap": "Dewi Lestari",
        "no_telepon": "081234560004",
        "alamat": "Ds. Sukodadi RT 01 RW 04, Kec. Sukodadi, Kab. Lamongan",
    },
    {
        "nik_or_nip": "3524051906940005",
        "email": "hendra.wijaya@warga.lamongan.id",
        "nama_lengkap": "Hendra Wijaya",
        "no_telepon": "081234560005",
        "alamat": "Ds. Deket Kulon RT 02 RW 01, Kec. Deket, Kab. Lamongan",
    },
    {
        "nik_or_nip": "3524062809990006",
        "email": "rina.kartika@warga.lamongan.id",
        "nama_lengkap": "Rina Kartika",
        "no_telepon": "081234560006",
        "alamat": "Ds. Brondong RT 05 RW 03, Kec. Brondong, Kab. Lamongan",
    },
]


DEMO_REPORTS = [
    {
        "warga_email": "budi.santoso@warga.lamongan.id",
        "judul": "Jalan berlubang parah dan aspal ambruk di poros Lamongan-Tikung",
        "isi_laporan": "Jalan poros kabupaten dekat perempatan Tikung berlubang dalam sekitar 25 cm dan ambruk setelah hujan deras, sangat membahayakan pengendara motor saat malam hari.",
        "lat": -7.1482,
        "long": 112.4165,
        "status": "diproses",
        "catatan_petugas": "Tim URC Bina Marga sudah melakukan survei lokasi dan menjadwalkan penambalan aspal hotmix besok pagi.",
        "days_ago": 1,
    },
    {
        "warga_email": "siti.aminah@warga.lamongan.id",
        "judul": "Tanggul sungai meluap dan banjir merendam jalan desa di Babat",
        "isi_laporan": "Terjadi banjir bandang akibat tanggul saluran irigasi jebol di sekitar Pasar Babat, air setinggi lutut orang dewasa dan drainase tersumbat parah.",
        "lat": -7.1068,
        "long": 112.1674,
        "status": "diterima",
        "catatan_petugas": None,
        "days_ago": 0,
    },
    {
        "warga_email": "ahmad.fauzi@warga.lamongan.id",
        "judul": "Lampu penerangan jalan umum (PJU) padam total sepanjang Jalan Raya Paciran",
        "isi_laporan": "Terdapat 6 tiang lampu PJU mati total sejak 4 malam terakhir di depan area wisata Paciran menuju Brondong sehingga jalan sangat gelap dan rawan kecelakaan.",
        "lat": -6.8756,
        "long": 112.3452,
        "status": "selesai",
        "catatan_petugas": "Petugas teknis Dishub telah mengganti panel kontaktor dan 6 unit lampu LED PJU. Lampu sudah menyala normal kembali.",
        "rating_kepuasan": 5,
        "ulasan_warga": "Respons sangat cepat! Malam ini jalanan Paciran sudah terang benderang kembali, terima kasih Dishub Lamongan.",
        "days_ago": 5,
    },
    {
        "warga_email": "dewi.lestari@warga.lamongan.id",
        "judul": "Tumpukan sampah liar dan bau menyengat di pinggir jalan Sukodadi",
        "isi_laporan": "Kontainer TPS di dekat pasar Sukodadi sudah meluber ke bahu jalan selama seminggu dan menimbulkan bau menyengat bagi warga dan pengguna jalan.",
        "lat": -7.0985,
        "long": 112.3264,
        "status": "selesai",
        "catatan_petugas": "Armada truk pengangkut DLH telah mengangkut seluruh tumpukan sampah dan membersihkan area sekitar TPS.",
        "rating_kepuasan": 4,
        "ulasan_warga": "Sudah bersih dan diangkut, semoga jadwal pengangkutannya bisa lebih rutin setiap dua hari.",
        "days_ago": 4,
    },
    {
        "warga_email": "hendra.wijaya@warga.lamongan.id",
        "judul": "Pohon peneduh besar tumbang menutup sebagian jalan di Deket",
        "isi_laporan": "Pohon besar di tepi jalan nasional Deket tumbang diterjang angin kencang dan menimpa kabel, arus lalu lintas macet total dan sangat berbahaya.",
        "lat": -7.1145,
        "long": 112.4632,
        "status": "diproses",
        "catatan_petugas": "Tim evakuasi DLH bersama BPBD sedang menuju lokasi membawa gergaji mesin untuk pemotongan batang pohon.",
        "days_ago": 0,
    },
    {
        "warga_email": "rina.kartika@warga.lamongan.id",
        "judul": "Atap ruang kelas SDN di Brondong bocor parah saat hujan",
        "isi_laporan": "Plafon dan genteng dua ruang kelas SD Negeri di wilayah Brondong rusak parah dan bocor setiap turun hujan sehingga mengganggu kegiatan belajar siswa.",
        "lat": -6.8834,
        "long": 112.2819,
        "status": "diproses",
        "catatan_petugas": "Dinas Pendidikan telah mengirim tim sarana prasarana untuk verifikasi kerusakan dan penyusunan RAB rehabilitasi darurat.",
        "days_ago": 3,
    },
    {
        "warga_email": "budi.santoso@warga.lamongan.id",
        "judul": "Antrean pelayanan cetak e-KTP di loket kecamatan cukup padat",
        "isi_laporan": "Mohon penambahan loket perekaman dan cetak e-KTP serta Kartu Keluarga pada hari Senin karena warga yang mengurus adminduk menunggu cukup lama.",
        "lat": -7.1192,
        "long": 112.4161,
        "status": "selesai",
        "catatan_petugas": "Disdukcapil telah menambah 1 petugas operator tambahan pada jam sibuk pagi hari serta mengoptimalkan aktivasi IKD.",
        "rating_kepuasan": 5,
        "ulasan_warga": "Pelayanan sekarang jauh lebih cepat dan petugas sangat ramah. Gratis tanpa pungutan!",
        "days_ago": 7,
    },
    {
        "warga_email": "siti.aminah@warga.lamongan.id",
        "judul": "Pedagang kaki lima menempati trotoar depan Alun-Alun Lamongan",
        "isi_laporan": "Beberapa lapak PKL berjualan di atas trotoar pejalan kaki dan menimbulkan kebisingan hingga larut malam di sisi utara Alun-Alun Lamongan.",
        "lat": -7.1198,
        "long": 112.4168,
        "status": "selesai",
        "catatan_petugas": "Regu patroli Satpol PP telah melakukan penertiban persuasif dan mengarahkan PKL ke zona kuliner resmi yang telah disediakan.",
        "rating_kepuasan": 4,
        "ulasan_warga": "Trotoar kini kembali lega untuk pejalan kaki, penertibannya juga humanis.",
        "days_ago": 6,
    },
    {
        "warga_email": "ahmad.fauzi@warga.lamongan.id",
        "judul": "Distribusi air bersih PDAM macet di perumahan Karanggeneng",
        "isi_laporan": "Aliran air bersih PDAM di permukiman warga Karanggeneng mengecil dan mati total sejak kemarin sore sehingga warga kesulitan kebutuhan rumah tangga.",
        "lat": -7.0014,
        "long": 112.3712,
        "status": "diterima",
        "catatan_petugas": None,
        "days_ago": 1,
    },
    {
        "warga_email": "dewi.lestari@warga.lamongan.id",
        "judul": "Usulan pendataan lansia kurang mampu untuk bantuan sosial DTKS",
        "isi_laporan": "Terdapat warga lansia sebatang kara di Desa Sukodadi yang belum masuk data penerima bansos PKH maupun BPNT, mohon pendampingan verifikasi Dinas Sosial.",
        "lat": -7.1012,
        "long": 112.3198,
        "status": "diproses",
        "catatan_petugas": "Pendamping sosial kecamatan telah berkoordinasi dengan operator SIKS-NG desa untuk asesmen dan pengusulan Musdes bulan ini.",
        "days_ago": 2,
    },
    {
        "warga_email": "hendra.wijaya@warga.lamongan.id",
        "judul": "Permintaan fogging DBD dan pemeriksaan jentik nyamuk di Turi",
        "isi_laporan": "Dalam seminggu terakhir ada 3 warga di lingkungan Desa Turi yang dirawat karena demam berdarah, mohon tindak lanjut Puskesmas dan Dinas Kesehatan.",
        "lat": -7.0815,
        "long": 112.3821,
        "status": "selesai",
        "catatan_petugas": "Tim surveilans Puskesmas Turi bersama Dinas Kesehatan telah melaksanakan PE (Penyelidikan Epidemiologi), PSN, dan fogging fokus.",
        "rating_kepuasan": 5,
        "ulasan_warga": "Alhamdulillah tim kesehatan langsung turun keesokan harinya dan melakukan fogging menyeluruh.",
        "days_ago": 8,
    },
    {
        "warga_email": "rina.kartika@warga.lamongan.id",
        "judul": "Kelangkaan pupuk bersubsidi dan serangan hama wereng di sawah Sugio",
        "isi_laporan": "Para petani di Kecamatan Sugio kesulitan mendapatkan alokasi pupuk bersubsidi dan tanaman padi mulai diserang hama wereng coklat.",
        "lat": -7.1932,
        "long": 112.3391,
        "status": "diterima",
        "catatan_petugas": None,
        "days_ago": 1,
    },
    {
        "warga_email": "budi.santoso@warga.lamongan.id",
        "judul": "Lampu merah (traffic light) error di simpang tiga Ngimbang",
        "isi_laporan": "Lampu lalu lintas di simpang tiga Kecamatan Ngimbang berkedip kuning terus-menerus sejak pagi sehingga menyebabkan kemacetan kendaraan besar.",
        "lat": -7.3118,
        "long": 112.2267,
        "status": "selesai",
        "catatan_petugas": "Teknisi APILL Dishub telah mereset modul kontroler traffic light dan mengganti sekring yang putus.",
        "rating_kepuasan": 5,
        "ulasan_warga": "Traffic light sudah kembali normal dan lalu lintas lancar.",
        "days_ago": 9,
    },
    {
        "warga_email": "siti.aminah@warga.lamongan.id",
        "judul": "Jembatan penghubung desa di Kedungpring retak pada bagian oprit",
        "isi_laporan": "Oprit jembatan penghubung antar desa di Kedungpring mengalami retakan lebar dan ambles ringan akibat dilewati truk bermuatan berat.",
        "lat": -7.1984,
        "long": 112.2385,
        "status": "diterima",
        "catatan_petugas": None,
        "days_ago": 2,
    },
    {
        "warga_email": "ahmad.fauzi@warga.lamongan.id",
        "judul": "Kendala pengisian kode KBLI UMKM saat mendaftar NIB di OSS",
        "isi_laporan": "Saya pelaku usaha mikro pengolahan ikan di Paciran membutuhkan pendampingan pengurusan NIB dan pemilihan kode KBLI di loket DPMPTSP.",
        "lat": -6.8791,
        "long": 112.3390,
        "status": "selesai",
        "catatan_petugas": "Petugas DPMPTSP telah menghubungi pemohon dan menjadwalkan pendampingan gratis di loket OSS MPP Lamongan.",
        "rating_kepuasan": 5,
        "ulasan_warga": "Dibantu sampai NIB terbit gratis dan jelas sekali arahannya.",
        "days_ago": 10,
    },
    {
        "warga_email": "dewi.lestari@warga.lamongan.id",
        "judul": "Wifi publik ruang terbuka taman kota sering putus koneksi",
        "isi_laporan": "Layanan internet wifi gratis di area taman kota dekat perpustakaan daerah sering terputus saat digunakan pelajar mengerjakan tugas.",
        "lat": -7.1206,
        "long": 112.4152,
        "status": "diproses",
        "catatan_petugas": "Tim jaringan Diskominfo sedang mengecek perangkat access point dan kestabilan bandwidth di lokasi.",
        "days_ago": 1,
    },
    {
        "warga_email": "hendra.wijaya@warga.lamongan.id",
        "judul": "Laporan uji coba fasilitas pribadi pagar rumah tetangga",
        "isi_laporan": "Permohonan perbaikan pagar pribadi rumah tinggal di lingkungan perumahan pribadi.",
        "lat": -7.1250,
        "long": 112.4410,
        "status": "ditolak",
        "catatan_petugas": "Mohon maaf, laporan tidak dapat ditindaklanjuti karena objek merupakan aset properti pribadi bukan fasilitas umum pemerintah daerah.",
        "days_ago": 6,
    },
    {
        "warga_email": "rina.kartika@warga.lamongan.id",
        "judul": "Saluran selokan depan balai desa Modo mampet (sudah kerja bakti)",
        "isi_laporan": "Selokan di depan balai desa Modo sempat tersumbat daun kering dan plastik, namun warga sudah bergotong royong membersihkannya pagi ini.",
        "lat": -7.2305,
        "long": 112.1488,
        "status": "dibatalkan",
        "catatan_petugas": None,
        "days_ago": 3,
    },
]


def seed():
    db = SessionLocal()
    try:
        password_hash = get_password_hash("WargaLamongan123!")
        warga_map = {}
        created_users = 0

        for w in DEMO_WARGA:
            existing = db.query(User).filter(User.email == w["email"]).first()
            if not existing:
                existing = User(
                    nik_or_nip=w["nik_or_nip"],
                    email=w["email"],
                    password_hash=password_hash,
                    role="warga",
                    is_active=True,
                    nama_lengkap=w["nama_lengkap"],
                    no_telepon=w["no_telepon"],
                    alamat=w["alamat"],
                )
                db.add(existing)
                db.commit()
                db.refresh(existing)
                created_users += 1
            warga_map[w["email"]] = existing

        super_admin = db.query(User).filter(User.role == "super_admin").first()
        admin_id_ref = super_admin.id if super_admin else None

        created_reports = 0
        now = datetime.utcnow()

        for item in DEMO_REPORTS:
            exists = db.query(Report).filter(Report.judul == item["judul"]).first()
            if exists:
                continue

            warga = warga_map[item["warga_email"]]
            dept_id, urgensi = analyze_report_ai(
                item["judul"],
                item["isi_laporan"],
                db,
                lat=item.get("lat"),
                long=item.get("long"),
            )
            created_ts = now - timedelta(days=item.get("days_ago", 1), hours=2)

            rep = Report(
                user_id=warga.id,
                dept_id=dept_id,
                judul=item["judul"],
                isi_laporan=item["isi_laporan"],
                status=item["status"],
                urgensi=urgensi,
                lat=item["lat"],
                long=item["long"],
                catatan_petugas=item.get("catatan_petugas"),
                rating_kepuasan=item.get("rating_kepuasan"),
                ulasan_warga=item.get("ulasan_warga"),
                rated_at=(created_ts + timedelta(hours=18)) if item.get("rating_kepuasan") else None,
                created_at=created_ts,
            )
            db.add(rep)
            db.commit()
            db.refresh(rep)
            created_reports += 1

            # Audit log trail yang realistis
            db.add(AuditLog(
                report_id=rep.id,
                admin_id=None,
                status_baru="diterima",
                timestamp=created_ts,
            ))
            if item["status"] in ("diproses", "selesai"):
                db.add(AuditLog(
                    report_id=rep.id,
                    admin_id=admin_id_ref,
                    status_baru="diproses",
                    timestamp=created_ts + timedelta(hours=4),
                ))
            if item["status"] == "selesai":
                db.add(AuditLog(
                    report_id=rep.id,
                    admin_id=admin_id_ref,
                    status_baru="selesai",
                    timestamp=created_ts + timedelta(hours=14),
                ))
            elif item["status"] == "ditolak":
                db.add(AuditLog(
                    report_id=rep.id,
                    admin_id=admin_id_ref,
                    status_baru="ditolak",
                    timestamp=created_ts + timedelta(hours=5),
                ))
            elif item["status"] == "dibatalkan":
                db.add(AuditLog(
                    report_id=rep.id,
                    admin_id=None,
                    status_baru="dibatalkan",
                    timestamp=created_ts + timedelta(hours=2),
                ))
            db.commit()

        print(f"Seeder selesai: +{created_users} akun warga baru, +{created_reports} laporan demo baru.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
