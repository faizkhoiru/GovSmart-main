from app.crud.user import create_admin_dinas
from app.schemas.user import AdminDinasCreate
from app.core.security import create_access_token
import io
import os
import tempfile
import pytest
from app import models
import app.core.upload as upload_mod


@pytest.fixture(autouse=True)
def _uploads_dir(monkeypatch):
    """Route uploads to a writable temp dir so tests pass off Docker container paths."""
    tmp = tempfile.mkdtemp(prefix="govsmart-uploads-")
    monkeypatch.setattr(upload_mod, "UPLOAD_DIR", tmp)
    yield tmp

def test_submit_report_typo_kebkaran_routes_to_satpol(client, warga_headers):
    response = client.post("/api/v1/reports/", json={
        "judul": "Kebkaran",
        "isi_laporan": "Kebkaran terjadi di rumah warga dan membutuhkan pemadam segera.",
    }, headers=warga_headers)
    assert response.status_code == 201
    dept = next(d for d in client.get("/api/v1/departments/").json() if d["id"] == response.json()["dept_id"])
    assert dept["nama_dinas"] == "Dinas Satuan Polisi Pamong Praja"


def test_submit_report_manual_department_routing(client, warga_headers):
    depts = client.get("/api/v1/departments/").json()
    target = next(d for d in depts if d["nama_dinas"] == "Dinas Kesehatan")
    response = client.post("/api/v1/reports/", json={
        "judul": "Pelayanan kesehatan terganggu",
        "isi_laporan": "Pelayanan kesehatan di puskesmas terganggu dan perlu segera ditindaklanjuti.",
        "dept_id": target["id"],
    }, headers=warga_headers)
    assert response.status_code == 201
    assert response.json()["dept_id"] == target["id"]


def test_submit_report_rejects_unknown_department(client, warga_headers):
    response = client.post("/api/v1/reports/", json={
        "judul": "Dinas tujuan tidak valid",
        "isi_laporan": "Isi pengaduan minimal dua puluh karakter untuk pengujian.",
        "dept_id": 999999,
    }, headers=warga_headers)
    assert response.status_code == 422


def test_submit_report_ai_routing_and_urgency(client, warga_headers):
    payload = {
        "judul": "Jalan berlubang parah dan ambruk di Babat",
        "isi_laporan": "Mohon ditindaklanjuti jalan raya utama babat mengalami kerusakan parah, berlubang dan ambruk sangat membahayakan warga.",
        "lat": -7.1123,
        "long": 112.1554
    }
    response = client.post("/api/v1/reports/", json=payload, headers=warga_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["judul"] == payload["judul"]
    assert data["urgensi"] == "darurat"
    assert data["dept_id"] is not None

def test_admin_update_status_and_audit(client, db, warga_headers, super_admin_headers):
    # 1. Warga submit report
    rep_res = client.post("/api/v1/reports/", json={
        "judul": "Penumpukan Sampah Bau Menyengat di Pasar",
        "isi_laporan": "Sampah tidak diangkut selama seminggu menyebabkan bau sangat menyengat dan mengganggu pedagang pasar."
    }, headers=warga_headers)
    assert rep_res.status_code == 201
    report_id = rep_res.json()["id"]
    routed_dept_id = rep_res.json()["dept_id"]

    # 2. Super Admin create Admin Dinas
    depts = client.get("/api/v1/departments/").json()
    dept_pu = next(d for d in depts if d["nama_dinas"] == "Dinas Lingkungan Hidup")

    admin_in = AdminDinasCreate(
        nip="198505052010011005",
        email="admin.pu@lamongan.go.id",
        password="AdminPassword123!",
        dept_id=dept_pu["id"]
    )
    admin_res = client.post("/api/v1/admin/admin-dinas", json={
        "nip": admin_in.nip,
        "email": admin_in.email,
        "password": admin_in.password,
        "dept_id": admin_in.dept_id
    }, headers=super_admin_headers)
    assert admin_res.status_code == 201

    # Login Admin Dinas
    token = create_access_token(subject=admin_in.email)
    admin_headers = {"Authorization": f"Bearer {token}"}

    # 3. Admin Dinas update report status to 'diproses'
    update_res = client.patch(f"/api/v1/reports/{report_id}/status", json={"status": "diproses"}, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "diproses"

    # 4. Check audit log
    audit_res = client.get(f"/api/v1/admin/audit-logs/{report_id}", headers=admin_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    assert logs[0]["status_baru"] == "diproses"

    # 5. Admin Dinas hanya melihat laporan pada dinasnya (list scoped)
    list_res = client.get("/api/v1/reports/", headers=admin_headers)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert any(r["id"] == report_id for r in reports)

def test_admin_dinas_cannot_access_other_dept_report(client, db, warga_headers, super_admin_headers):
    """Admin Dinas tidak boleh melihat/mengubah laporan yang dialokasikan ke dinas lain."""
    # Create a 'sampah' (Lingkungan Hidup) report routed via AI
    rep_res = client.post("/api/v1/reports/", json={
        "judul": "Penumpukan Sampah Bau Menyengat di Pasar",
        "isi_laporan": "Sampah tidak diangkut selama seminggu menyebabkan bau sangat menyengat."
    }, headers=warga_headers)
    routed_dept_id = rep_res.json()["dept_id"]

    # Create Admin Dinas for a DIFFERENT departemen (Pendidikan)
    depts = client.get("/api/v1/departments/").json()
    other_dept = next(d for d in depts if d["id"] != routed_dept_id)

    admin_in = AdminDinasCreate(
        nip="198505052010011010",
        email="admin.pend@lamongan.go.id",
        password="AdminPassword123!",
        dept_id=other_dept["id"]
    )
    client.post("/api/v1/admin/admin-dinas", json={
        "nip": admin_in.nip, "email": admin_in.email,
        "password": admin_in.password, "dept_id": admin_in.dept_id
    }, headers=super_admin_headers)

    token = create_access_token(subject=admin_in.email)
    admin_headers = {"Authorization": f"Bearer {token}"}

    # Detail should be 403
    detail = client.get(f"/api/v1/reports/{rep_res.json()['id']}", headers=admin_headers)
    assert detail.status_code == 403

    # Status update should be 403
    upd = client.patch(f"/api/v1/reports/{rep_res.json()['id']}/status",
                       json={"status": "diproes"}, headers=admin_headers)
    assert upd.status_code == 403

    # Audit log should be 403
    audit = client.get(f"/api/v1/admin/audit-logs/{rep_res.json()['id']}", headers=admin_headers)
    assert audit.status_code == 403

def test_upload_foto_success(client, warga_headers, _uploads_dir):
    """Upload foto JPEG valid (<5MB) oleh pemilik laporan harus berhasil."""
    # 1. Buat laporan terlebih dahulu
    rep_res = client.post("/api/v1/reports/", json={
        "judul": "Kerusakan Fasilitas Taman Kota",
        "isi_laporan": "Bangku taman di alun-alun lamongan rusak parah dan berbahaya bagi pengunjung.",
    }, headers=warga_headers)
    assert rep_res.status_code == 201
    report_id = rep_res.json()["id"]

    # 2. Buat dummy file JPEG di memori (konten minimal JPEG header)
    fake_jpeg = io.BytesIO(
        b'\xff\xd8\xff\xe0' + b'\x00' * 100  # JPEG magic bytes + padding
    )

    # 3. Upload foto sebagai multipart/form-data
    upload_res = client.post(
        f"/api/v1/reports/{report_id}/upload-foto",
        files={"foto": ("bukti.jpg", fake_jpeg, "image/jpeg")},
        headers=warga_headers
    )
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["foto_bukti"] is not None
    assert data["foto_bukti"].endswith(".jpg")

    # 4. File seharusnya tersimpan di direktori upload test
    assert os.path.exists(os.path.join(_uploads_dir, data["foto_bukti"]))


def test_upload_foto_invalid_mime(client, warga_headers, _uploads_dir):
    """Upload file PDF (bukan gambar) harus ditolak dengan 422."""
    # 1. Buat laporan terlebih dahulu
    rep_res = client.post("/api/v1/reports/", json={
        "judul": "Genangan Air di Jalan Protokol",
        "isi_laporan": "Genangan air di depan kantor kecamatan sudah berlangsung berhari-hari dan mengganggu lalu lintas.",
    }, headers=warga_headers)
    assert rep_res.status_code == 201
    report_id = rep_res.json()["id"]

    # 2. Coba upload file PDF (tipe tidak diizinkan)
    fake_pdf = io.BytesIO(b'%PDF-1.4 fake content')
    upload_res = client.post(
        f"/api/v1/reports/{report_id}/upload-foto",
        files={"foto": ("dokumen.pdf", fake_pdf, "application/pdf")},
        headers=warga_headers
    )
    assert upload_res.status_code == 422
    assert "diizinkan" in upload_res.json()["detail"].lower()


def test_submit_report_kampus_and_emergency(client, warga_headers):
    """Laporan fasilitas kampus terbakar harus ter-routing ke Dinas Pendidikan dengan urgensi darurat."""
    payload = {
        "judul": "Fasilitas Kampus ada yang rusak/terbakar",
        "isi_laporan": "Fasilitas Kampus ada yang rusak/terbakar di gedung perkuliahan",
    }
    response = client.post("/api/v1/reports/", json=payload, headers=warga_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["urgensi"] == "darurat"
    assert data["dept_id"] is not None

    # Verifikasi nama dinasnya adalah Dinas Pendidikan
    depts = client.get("/api/v1/departments/").json()
    routed_dept = next(d for d in depts if d["id"] == data["dept_id"])
    assert routed_dept["nama_dinas"] == "Dinas Pendidikan"


def test_submit_report_typo_fuzzy_routing(client, warga_headers):
    """Laporan dengan typo 'Tanah Longsot' harus tetap ter-routing ke Dinas PU Sumber Daya Air."""
    payload = {
        "judul": "Tanah Longsot",
        "isi_laporan": "Tanah Longsot di Daerah lereng sungai, terjadi longsor besar",
    }
    response = client.post("/api/v1/reports/", json=payload, headers=warga_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["urgensi"] == "darurat"
    assert data["dept_id"] is not None

    depts = client.get("/api/v1/departments/").json()
    routed_dept = next(d for d in depts if d["id"] == data["dept_id"])
    assert routed_dept["nama_dinas"] == "Dinas Pekerjaan Umum Sumber Daya Air"


def test_submit_report_fallback_routing(client, warga_headers):
    """Laporan tanpa kata kunci spesifik harus fallback ke Dinas Komunikasi dan Informatika."""
    payload = {
        "judul": "Informasi Umum",
        "isi_laporan": "Halo selamat siang mohon konfirmasi",
    }
    response = client.post("/api/v1/reports/", json=payload, headers=warga_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["dept_id"] is not None

    depts = client.get("/api/v1/departments/").json()
    routed_dept = next(d for d in depts if d["id"] == data["dept_id"])
    assert routed_dept["nama_dinas"] == "Dinas Komunikasi dan Informatika"


def test_warga_history_limited_and_can_cancel_before_processing(client, warga_headers):
    for index in range(6):
        response = client.post("/api/v1/reports/", json={
            "judul": f"Pengaduan nomor {index + 1}",
            "isi_laporan": "Isi pengaduan minimal dua puluh karakter untuk pengujian.",
        }, headers=warga_headers)
        assert response.status_code == 201

    history = client.get("/api/v1/reports/history", headers=warga_headers)
    assert history.status_code == 200
    assert len(history.json()) == 5

    report_id = history.json()[0]["id"]
    cancel = client.post(f"/api/v1/reports/{report_id}/cancel", headers=warga_headers)
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "dibatalkan"


def test_warga_cannot_cancel_processed_report(client, warga_headers, super_admin_headers):
    report = client.post("/api/v1/reports/", json={
        "judul": "Pengaduan untuk diuji",
        "isi_laporan": "Isi pengaduan minimal dua puluh karakter untuk pengujian.",
    }, headers=warga_headers).json()
    response = client.patch(
        f"/api/v1/reports/{report['id']}/status",
        json={"status": "diproses"},
        headers=super_admin_headers,
    )
    assert response.status_code == 200
    cancel = client.post(f"/api/v1/reports/{report['id']}/cancel", headers=warga_headers)
    assert cancel.status_code == 409


def test_sync_routing_endpoint(client, super_admin_headers):
    """Super admin dapat memicu sync-routing untuk laporan yang belum ter-routing."""
    response = client.post("/api/v1/reports/sync-routing", headers=super_admin_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "total_unrouted_found" in res_data
    assert "total_updated" in res_data

