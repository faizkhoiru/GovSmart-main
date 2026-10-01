def test_register_warga_success(client):
    payload = {
        "nik_or_nip": "3524020202900002",
        "email": "budi.warga@lamongan.go.id",
        "password": "PasswordSuper123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["nik_or_nip"] == payload["nik_or_nip"]
    assert data["role"] == "warga"

def test_register_duplicate_email(client, warga_user):
    payload = {
        "nik_or_nip": "3524030303910003",
        "email": warga_user.email,
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "registered" in response.json()["detail"].lower()

def test_login_success(client, warga_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": warga_user.email, "password": "Password123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client, warga_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": warga_user.email, "password": "WrongPassword!"}
    )
    assert response.status_code == 401

def test_register_weak_password_rejected(client):
    """Password tanpa simbol harus ditolak dengan 422 sesuai PRD."""
    payload = {
        "nik_or_nip": "3524040404920004",
        "email": "lemah.password@lamongan.go.id",
        "password": "Password123"  # Tidak ada simbol -> lemah
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert any(
        "simbol" in str(err).lower() or "password" in str(err).lower()
        for err in body.get("detail", [])
    )

def test_register_strong_password_accepted(client):
    """Password kuat (huruf besar, kecil, angka, simbol) harus berhasil dengan 201."""
    payload = {
        "nik_or_nip": "3524050505930005",
        "email": "kuat.password@lamongan.go.id",
        "password": "Kuat@Sekali99!"  # Semua syarat terpenuhi
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["role"] == "warga"

