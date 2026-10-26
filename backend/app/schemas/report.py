from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReportCreate(BaseModel):
    judul: str = Field(..., min_length=5, max_length=100, description="Judul laporan (5-100 karakter)")
    isi_laporan: str = Field(..., min_length=20, max_length=2000, description="Isi laporan (20-2000 karakter)")
    dept_id: Optional[int] = None
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    long: Optional[float] = Field(None, ge=-180.0, le=180.0)

class ReportUpdate(BaseModel):
    judul: str = Field(..., min_length=5, max_length=100, description="Judul laporan (5-100 karakter)")
    isi_laporan: str = Field(..., min_length=20, max_length=2000, description="Isi laporan (20-2000 karakter)")
    dept_id: Optional[int] = None
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    long: Optional[float] = Field(None, ge=-180.0, le=180.0)

class ReportUpdateStatus(BaseModel):
    status: str = Field(..., description="Status baru: diterima, diproses, selesai, ditolak")
    catatan_petugas: Optional[str] = Field(None, max_length=1000, description="Catatan tindak lanjut atau alasan petugas")

class ReportResponse(BaseModel):
    id: int
    user_id: int
    dept_id: Optional[int] = None
    judul: str
    isi_laporan: str
    status: str
    urgensi: str
    lat: Optional[float] = None
    long: Optional[float] = None
    # Nama file foto bukti yang telah diupload (None jika belum ada lampiran)
    foto_bukti: Optional[str] = None
    # Catatan / keterangan tindak lanjut dari dinas
    catatan_petugas: Optional[str] = None
    # Nama file dokumen/foto feedback dari admin dinas (None jika belum ada)
    foto_feedback: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

