def test_super_admin_create_admin_dinas(client, super_admin_headers):
    payload = {
        "nip": "199203032018021002",
        "email": "admin.dhl@lamongan.go.id",
        "password": "PasswordAdmin123!"
    }
    response = client.post("/api/v1/admin/admin-dinas", json=payload, headers=super_admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "admin"

def test_warga_cannot_create_admin_dinas(client, warga_headers):
    payload = {
        "nip": "199504042020011003",
        "email": "hacker@lamongan.go.id",
        "password": "HackPassword123!"
    }
    response = client.post("/api/v1/admin/admin-dinas", json=payload, headers=warga_headers)
    assert response.status_code == 403

def test_get_departments_list(client):
    response = client.get("/api/v1/departments/")
    assert response.status_code == 200
    depts = response.json()
    assert len(depts) > 0
    assert any(d["nama_dinas"] == "Dinas Pekerjaan Umum & Penataan Ruang" for d in depts)
