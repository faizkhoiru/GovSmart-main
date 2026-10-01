from app.crud.user import create_admin_dinas
from app.schemas.user import AdminDinasCreate
from app.core.security import create_access_token
import io

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

    # 2. Super Admin create Admin Dinas
    admin_in = AdminDinasCreate(
        nip="198505052010011005",
        email="admin.pu@lamongan.go.id",
        password="AdminPassword123!"
    )
    admin_res = client.post("/api/v1/admin/admin-dinas", json={
        "nip": admin_in.nip,
        "email": admin_in.email,
        "password": admin_in.password
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

def test_upload_foto_success(client, warga_headers):
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

def test_upload_foto_invalid_mime(client, warga_headers):
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

