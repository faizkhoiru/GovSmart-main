class _FakeResp:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None, headers=None):
        q = (json or {}).get("pertanyaan", "")
        return _FakeResp({
            "jawaban": f"Syarat NIB/OSS untuk: {q}",
            "intent": "faq_nib",
            "mode": "ekstraktif",
            "sumber": [{"no": 1, "judul": "Panduan NIB", "konteks": "OSS", "layanan": "DPMPTSP", "halaman": "1"}],
        })


def test_ask_chatbot_umkm_licensing(client, warga_headers, monkeypatch):
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    payload = {"pertanyaan": "Bagaimana syarat urus NIB untuk usaha UMKM di Lamongan?"}
    response = client.post("/api/v1/chat/", json=payload, headers=warga_headers)
    assert response.status_code == 200
    data = response.json()
    assert "NIB" in data["jawaban"] or "OSS" in data["jawaban"]
    assert data["intent"] == "faq_nib"


def test_get_chat_history_separate_per_user(client, warga_user, warga_headers, db, monkeypatch):
    """Riwayat chatbot harus terisolasi per user - user A tidak melihat riwayat user B."""
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)

    from app.models.user import User
    from app.schemas.user import UserCreate
    from app.crud.user import create_user
    from app.core.security import create_access_token

    # Buat user kedua
    user_b_in = UserCreate(
        email="warga.b@lamongan.go.id",
        nik_or_nip="3524010101950002",
        password="Password123!"
    )
    user_b = create_user(db, user_b_in, role="warga")
    token_b = create_access_token(subject=user_b.email)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A kirim chat
    client.post("/api/v1/chat/", json={"pertanyaan": "Pertanyaan dari user A"}, headers=warga_headers)

    # User B kirim chat
    client.post("/api/v1/chat/", json={"pertanyaan": "Pertanyaan dari user B"}, headers=headers_b)

    # Cek riwayat user A hanya mengandung pertanyaannya sendiri
    res_a = client.get("/api/v1/chat/history", headers=warga_headers)
    assert res_a.status_code == 200
    hist_a = res_a.json()
    assert hist_a["count"] == 1
    assert "user A" in hist_a["results"][0]["prompt"]
    assert "user B" not in hist_a["results"][0]["prompt"]

    # Cek riwayat user B hanya mengandung pertanyaannya sendiri
    res_b = client.get("/api/v1/chat/history", headers=headers_b)
    assert res_b.status_code == 200
    hist_b = res_b.json()
    assert hist_b["count"] == 1
    assert "user B" in hist_b["results"][0]["prompt"]
    assert "user A" not in hist_b["results"][0]["prompt"]


def test_clear_chat_history_isolated_per_user(client, warga_user, warga_headers, db, monkeypatch):
    """DELETE /history hanya menghapus riwayat user yang terautentikasi, bukan user lain."""
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)

    from app.schemas.user import UserCreate
    from app.crud.user import create_user
    from app.core.security import create_access_token

    # User A kirim 2 chat
    client.post("/api/v1/chat/", json={"pertanyaan": "Pertanyaan A1"}, headers=warga_headers)
    client.post("/api/v1/chat/", json={"pertanyaan": "Pertanyaan A2"}, headers=warga_headers)

    # Buat user B dan kirim 1 chat
    user_b = create_user(db, UserCreate(
        email="warga.b2@lamongan.go.id",
        nik_or_nip="3524010101950003",
        password="Password123!"
    ), role="warga")
    token_b = create_access_token(subject=user_b.email)
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client.post("/api/v1/chat/", json={"pertanyaan": "Pertanyaan B1"}, headers=headers_b)

    # User A hapus riwayat
    del_res = client.delete("/api/v1/chat/history", headers=warga_headers)
    assert del_res.status_code == 204

    # User A riwayat harus kosong
    res_a = client.get("/api/v1/chat/history", headers=warga_headers)
    assert res_a.json()["count"] == 0

    # User B riwayat tetap ada (tidak tersentuh)
    res_b = client.get("/api/v1/chat/history", headers=headers_b)
    assert res_b.json()["count"] == 1
    assert "Pertanyaan B1" in res_b.json()["results"][0]["prompt"]
