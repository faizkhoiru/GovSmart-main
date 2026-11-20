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


def test_real_chatbot_intent_and_rag_accuracy():
    from scripts.chatbot import GovSmartChatbot
    from scripts.retriever import Retriever

    r = Retriever()
    r._model = False
    bot = GovSmartChatbot(retriever=r)

    res_persona = bot.tanya("kamu cowo apa cewe?", pakai_llm=False)
    assert res_persona["intent"] == "perkenalan"
    assert "BPUPK" not in res_persona["jawaban"]

    res_keluhan = bot.tanya("aduh", pakai_llm=False)
    assert res_keluhan["intent"] == "bantuan_awal"
    assert "BPUPK" not in res_keluhan["jawaban"]

    res_panduan = bot.tanya("cara menggunakan aplikasi ini", pakai_llm=False)
    assert res_panduan["intent"] == "jawab"
    assert "GovSmart" in res_panduan["jawaban"]
    assert "# " not in res_panduan["jawaban"]

    res_kkpr = bot.tanya("Berapa lama proses registrasi KKPR?", pakai_llm=False)
    assert res_kkpr["intent"] == "jawab"
    assert "1 (satu) hari kerja" in res_kkpr["jawaban"] or "10 (sepuluh) hari kerja" in res_kkpr["jawaban"]

    out_of_rag_cases = [
        "cara membuka koperasi desa",
        "Cara membuka kopdes merah putih",
        "syarat pinjaman kur bri untuk umkm",
        "cara membuat akta pendirian pt di kemenkumham",
        "cara daftar bpjs ketenagakerjaan",
        "berapa biaya balik nama sertifikat tanah di bpn",
        "cara lapor spt pajak tahunan di djp online",
        "syarat pengajuan kpr rumah subsidi",
        "rekomendasi wisata kuliner di lamongan",
        "jadwal kereta api lamongan surabaya",
        "resep nasi goreng enak",
        "gimana cara membuat negara?",
        "cara membuat negara?",
        "gimana cara jadi presiden?",
        "cara memperbaiki lampu rumah yang mati",
        "cara memperbaiki jalan pikiran",
        "cara daftar sekolah kedinasan",
        "cara menggunakan gps di mobil",
        "cara ganti password wifi",
        "cara ganti password email",
        "kenapa langit berwarna biru",
        "berapa jumlah penduduk indonesia",
        "apa makanan khas lamongan",
        "berapa luas wilayah lamongan",
        "cara buat laporan keuangan perusahaan",
        "info makanan",
        "info makanan dong",
        "cari makanan",
        "rekomendasi makanan",
        "rkeomendasi makanan",
        "makanan enak",
        "info minuman",
        "info roti",
        "info kue",
        "info tapanuli utara",
        "info jakarta utara",
        "gimana cara jadi anaknya puan?",
    ]
    for q in out_of_rag_cases:
        res_out = bot.tanya(q, pakai_llm=False)
        assert res_out["intent"] == "di_luar_topik", f"Harusnya di_luar_topik untuk {q!r}, dapat {res_out}"
        assert res_out["sumber"] == []

