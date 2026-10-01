def test_ask_chatbot_umkm_licensing(client, warga_headers):
    payload = {"prompt": "Bagaimana syarat urus NIB untuk usaha UMKM di Lamongan?"}
    response = client.post("/api/v1/chat/", json=payload, headers=warga_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["prompt"] == payload["prompt"]
    assert "NIB" in data["response"] or "OSS" in data["response"]

def test_get_chat_history(client, warga_headers):
    # Ask 2 questions
    client.post("/api/v1/chat/", json={"prompt": "Syarat buat KTP baru?"}, headers=warga_headers)
    client.post("/api/v1/chat/", json={"prompt": "Bagaimana cara lapor jalan rusak?"}, headers=warga_headers)

    history_res = client.get("/api/v1/chat/history", headers=warga_headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 2
