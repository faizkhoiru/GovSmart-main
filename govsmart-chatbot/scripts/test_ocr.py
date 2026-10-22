import glob
import pypdfium2 as pdfium
from ocrmac import ocrmac

# Cari PDF Perbup 40/2025, baik sudah di-rename maupun belum
kandidat = glob.glob("knowledge_base/pemerintah/*40*.pdf") + glob.glob("knowledge_base/pemerintah/*perbup*.pdf")
if not kandidat:
    raise SystemExit("PDF Perbup tidak ditemukan di knowledge_base/pemerintah/")
PDF = kandidat[0]
print("Memakai:", PDF)

pdf = pdfium.PdfDocument(PDF)
print("Jumlah halaman:", len(pdf))

page = pdf[9]                              # halaman ke-10
img = page.render(scale=2.5).to_pil()      # skala 2.5, kira-kira 180 dpi
img.save("data/raw/test_page.png")

hasil = ocrmac.OCR(img, recognition_level="accurate").recognize()
teks = "\n".join(t for t, conf, bbox in hasil)
print("Jumlah baris terbaca:", len(hasil))
print("-" * 40)
print(teks[:1500])
