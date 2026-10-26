from sqlalchemy import Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    dept_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    judul: Mapped[str] = mapped_column(String(100), nullable=False)
    isi_laporan: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="normal")
    urgensi: Mapped[str] = mapped_column(String(50), default="normal") # normal, penting, darurat
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    long: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Nama file bukti foto yang diupload (nullable, maks 5 MB, JPEG/PNG/WEBP)
    foto_bukti: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Catatan / keterangan tindak lanjut dari petugas dinas
    catatan_petugas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Nama file dokumen/foto feedback dari admin dinas (nullable, JPEG/PNG/WEBP/PDF, maks 5 MB)
    foto_feedback: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Waktu pembuatan laporan
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
