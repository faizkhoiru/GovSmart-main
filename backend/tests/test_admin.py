def test_super_admin_create_admin_dinas(client, super_admin_headers):
    depts = client.get("/api/v1/departments/").json()
    dept = next(d for d in depts if d["nama_dinas"] == "Dinas Lingkungan Hidup")
    payload = {
        "nip": "199203032018021002",
        "email": "admin.dhl@lamongan.go.id",
        "password": "PasswordAdmin123!",
        "dept_id": dept["id"]
    }
    response = client.post("/api/v1/admin/admin-dinas", json=payload, headers=super_admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "admin"
    assert data["dept_id"] == payload["dept_id"]

def test_create_admin_dinas_requires_dept_id(client, super_admin_headers):
    payload = {
        "nip": "199203032018021003",
        "email": "admin.notdept@lamongan.go.id",
        "password": "PasswordAdmin123!"
    }
    response = client.post("/api/v1/admin/admin-dinas", json=payload, headers=super_admin_headers)
    assert response.status_code == 422

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
    assert any(d["nama_dinas"] == "Dinas Kesehatan" for d in depts)
    assert any(d["nama_dinas"] == "Dinas Pendidikan" for d in depts)
