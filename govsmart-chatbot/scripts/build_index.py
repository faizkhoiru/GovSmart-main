#!/usr/bin/env python3
"""Tahap 4a - Embedding semua chunk dan simpan indeks.

Letakkan di scripts/build_index.py, jalankan dari root proyek:
    pip install sentence-transformers numpy
    python scripts/build_index.py

Input : data/chunks/chunks.jsonl            (hasil chunk_docs.py)
Output: data/index/embeddings.npy           (matriks embedding ternormalisasi, urutan = chunks.jsonl)
        data/index/index_meta.json          (model, jumlah, hash chunks.jsonl)

Catatan: untuk ~1.000 chunk, pencarian cukup dengan perkalian matriks numpy (milidetik),
jadi FAISS/Chroma belum diperlukan. Antarmuka retriever bisa ditukar nanti bila data membesar.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "chunks" / "chunks.jsonl"
OUT_DIR = ROOT / "data" / "index"

# Model multibahasa (termasuk Indonesia), batas 512 token -> chunk 900-1300 karakter tidak terpotong.
# Model E5 wajib memakai awalan "passage: " untuk dokumen dan "query: " untuk pertanyaan.
MODEL = "intfloat/multilingual-e5-small"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    if not CHUNKS.exists():
        raise SystemExit(f"{CHUNKS} tidak ada. Jalankan chunk_docs.py dulu.")
    raw = CHUNKS.read_bytes()
    chunks = [json.loads(ln) for ln in raw.decode("utf-8").splitlines() if ln.strip()]
    print(f"{len(chunks)} chunk dari {CHUNKS}")

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise SystemExit("Pasang dulu: pip install sentence-transformers numpy")

    print(f"Memuat model {args.model} (unduhan pertama bisa beberapa menit)...")
    model = SentenceTransformer(args.model, device="cpu")
    model.max_seq_length = 512

    texts = ["passage: " + c["teks_embed"] for c in chunks]
    emb = model.encode(texts, batch_size=args.batch, normalize_embeddings=True,
                       show_progress_bar=True).astype("float32")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUT_DIR / "embeddings.npy", emb)
    meta = {"model": args.model, "n": len(chunks), "dim": int(emb.shape[1]),
            "chunks_sha1": hashlib.sha1(raw).hexdigest()}
    (OUT_DIR / "index_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Selesai: {emb.shape} -> {OUT_DIR}")


if __name__ == "__main__":
    main()
