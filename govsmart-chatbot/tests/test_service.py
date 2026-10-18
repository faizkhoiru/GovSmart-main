import sys, os
os.environ.setdefault('CHATBOT_INTERNAL_TOKEN','rahasia')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+"/.."))
from fastapi.testclient import TestClient
from service import create_app, mask_pii

class FakeBot:
    def tanya(self, pertanyaan, pakai_llm=True):
        return {
            "jawaban": pertanyaan,
            "intent": "test",
            "mode": "ekstraktif",
            "sumber": [{"no":1,"judul":"Judul","konteks":"isi","layanan":"Dinas","halaman":"1"}]
        }

client = TestClient(create_app(bot=FakeBot()))

def test_health_ready():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["is_ready"] is True

def test_ask_valid():
    r = client.post("/ask",
        headers={"X-Internal-Token":"rahasia"},
        json={"pertanyaan": "Test berhasil"}
    )
    assert r.status_code == 200
    assert r.json()["jawaban"] == "Test berhasil"
    assert "intent" in r.json()
    assert "mode" in r.json()
    assert "sumber" in r.json()

def test_ask_invalid_empty():
    r = client.post("/ask",
        headers={"X-Internal-Token":"rahasia"},
        json={"pertanyaan": ""}
    )
    assert r.status_code == 422

def test_ask_invalid_too_long():
    r = client.post("/ask",
        headers={"X-Internal-Token": "rahasia"},
        json={"pertanyaan": "x" * 501}
    )
    assert r.status_code == 422

def test_ask_no_token():
    r = client.post("/ask", json={"pertanyaan": "halo"})
    assert r.status_code == 401

def test_ask_wrong_token():
    r = client.post("/ask", headers={"X-Internal-Token": "SALAH"}, json={"pertanyaan": "halo"})
    assert r.status_code == 401

def test_masking_cases():
    # 16 digit
    assert mask_pii("NIK 1234567890123456") == "NIK [NIK]"
    # 15 digit
    assert mask_pii("NIK 123456789012345") == "NIK 123456789012345"
    # 16 digit dengan spasi/hubung
    assert mask_pii("NIK 1234 5678 9012 3456") == "NIK [NIK]"
    assert mask_pii("NIK 1234-5678-9012-3456") == "NIK [NIK]"
    # Email
    assert mask_pii("email agungcoba12@gmail.com") == "email [EMAIL]"
    assert mask_pii("agung+1@sub.example.com") == "[EMAIL]"
