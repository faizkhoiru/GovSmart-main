import os
import uuid
from fastapi import UploadFile, HTTPException, status

# Tipe file yang diizinkan sesuai PRD (image/jpeg, image/png, image/webp)
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Batas ukuran file maksimum: 5 MB sesuai PRD
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Direktori penyimpanan file upload di dalam container
UPLOAD_DIR = "/app/uploads"


def validate_and_save_upload(file: UploadFile) -> str:
    """
    Validasi file upload sesuai aturan PRD:
    - Tipe MIME harus image/jpeg, image/png, atau image/webp
    - Ukuran file tidak boleh melebihi 5 MB

    Mengembalikan nama file unik yang tersimpan.
    Melempar HTTPException 422 jika validasi gagal.
    """
    # 1. Validasi tipe MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Tipe file '{file.content_type}' tidak diizinkan. "
                f"Hanya menerima: JPEG, PNG, WEBP."
            )
        )

    # 2. Validasi ekstensi file sebagai lapisan keamanan tambahan
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Ekstensi file '{ext}' tidak diizinkan. "
                f"Hanya menerima: .jpg, .jpeg, .png, .webp."
            )
        )

    # 3. Baca konten file & validasi ukuran
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ukuran file melebihi batas maksimum 5 MB. Ukuran file Anda: {len(contents) / (1024*1024):.2f} MB."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File tidak boleh kosong."
        )

    # 4. Simpan file dengan nama unik agar tidak terjadi tabrakan nama
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext.lower()}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    return unique_filename
