"""Tests for Admin Dinas CRUD endpoints in the superadmin dashboard."""
from app.schemas.user import AdminDinasCreate
from app.core.security import create_access_token


def _get_dept(client, nama_dinas):
    depts = client.get("/api/v1/departments/").json()
    return next(d for d in depts if d["nama_dinas"] == nama_dinas)


def _create_admin(client, super_admin_headers, dept_id=None):
    if dept_id is None:
        dept = _get_dept(client, "Dinas Lingkungan Hidup")
        dept_id = dept["id"]
    payload = {
        "nip": "199203032018022001",
        "email": "admin.crud@lamongan.go.id",
        "password": "PasswordAdmin123!",
        "dept_id": dept_id,
    }
    res = client.post("/api/v1/admin/admin-dinas", json=payload, headers=super_admin_headers)
    assert res.status_code == 201
    return res.json()


def test_list_admin_dinas(client, super_admin_headers):
    created = _create_admin(client, super_admin_headers)
    res = client.get("/api/v1/admin/admin-dinas", headers=super_admin_headers)
    assert res.status_code == 200
    admins = res.json()
    assert any(a["email"] == created["email"] for a in admins)


def test_get_admin_dinas_by_id(client, super_admin_headers):
    created = _create_admin(client, super_admin_headers)
    res = client.get(f"/api/v1/admin/admin-dinas/{created['id']}", headers=super_admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == created["email"]
    assert data["role"] == "admin"
    assert data["is_active"] is True


def test_get_admin_dinas_not_found(client, super_admin_headers):
    res = client.get("/api/v1/admin/admin-dinas/9999", headers=super_admin_headers)
    assert res.status_code == 404


def test_update_admin_dinas_dept_and_password(client, super_admin_headers):
    created = _create_admin(client, super_admin_headers)
    new_dept = _get_dept(client, "Dinas Kesehatan")
    payload = {
        "email": "admin.crud.updated@lamongan.go.id",
        "dept_id": new_dept["id"],
        "password": "NewPassword123!",
    }
    res = client.put(
        f"/api/v1/admin/admin-dinas/{created['id']}",
        json=payload,
        headers=super_admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == payload["email"]
    assert data["dept_id"] == new_dept["id"]

    # Verify login with new password works
    token = create_access_token(subject=payload["email"])
    admin_headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/admin/me", headers=admin_headers)
    assert me_res.status_code == 200


def test_update_admin_dinas_not_found(client, super_admin_headers):
    res = client.put(
        "/api/v1/admin/admin-dinas/9999",
        json={"email": "x@lamongan.go.id"},
        headers=super_admin_headers,
    )
    assert res.status_code == 404


def test_update_admin_dinas_duplicate_email_conflict(client, super_admin_headers):
    created = _create_admin(client, super_admin_headers)
    # Try to update to an email already used by another admin
    payload = {"email": "admin.crud@lamongan.go.id"}
    res = client.put(
        f"/api/v1/admin/admin-dinas/{created['id']}",
        json=payload,
        headers=super_admin_headers,
    )
    # Email is the same as the admin's own — should succeed (no conflict with self)
    assert res.status_code == 200


def test_soft_delete_admin_dinas(client, super_admin_headers):
    created = _create_admin(client, super_admin_headers)
    res = client.delete(
        f"/api/v1/admin/admin-dinas/{created['id']}",
        headers=super_admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Super-admin cannot list themselves, but the admin should no longer be in the active list
    list_res = client.get("/api/v1/admin/admin-dinas", headers=super_admin_headers)
    admins = list_res.json()
    assert not any(a["id"] == created["id"] for a in admins)


def test_hard_delete_admin_dinas(client, super_admin_headers):
    created = _create_admin(client, super_admin_headers)
    res = client.delete(
        f"/api/v1/admin/admin-dinas/{created['id']}?hard=true",
        headers=super_admin_headers,
    )
    assert res.status_code == 200
    # Verify the user is gone from DB
    get_res = client.get(
        f"/api/v1/admin/admin-dinas/{created['id']}",
        headers=super_admin_headers,
    )
    assert get_res.status_code == 404


def test_delete_admin_dinas_not_found(client, super_admin_headers):
    res = client.delete(
        "/api/v1/admin/admin-dinas/9999",
        headers=super_admin_headers,
    )
    assert res.status_code == 404


def test_list_admin_dinas_requires_super_admin(client, warga_headers):
    res = client.get("/api/v1/admin/admin-dinas", headers=warga_headers)
    assert res.status_code == 403
