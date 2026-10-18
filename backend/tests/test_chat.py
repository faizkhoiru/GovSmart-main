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


def test_get_chat_history(client, warga_headers, monkeypatch):
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    client.post("/api/v1/chat/", json={"pertanyaan": "Syarat buat KTP baru?"}, headers=warga_headers)
    client.post("/api/v1/chat/", json={"pertanyaan": "Bagaimana cara lapor jalan rusak?"}, headers=warga_headers)

    history_res = client.get("/api/v1/chat/history", headers=warga_headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert history["count"] >= 2
    assert history["results"][0]["prompt"]
