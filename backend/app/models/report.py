# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    judul = Column(String(100), nullable=False)
    isi_laporan = Column(Text, nullable=False)
    status = Column(String(50), default="normal")
    urgensi = Column(String(50), default="normal") # normal, penting, darurat
    lat = Column(Float, nullable=True)
    long = Column(Float, nullable=True)
    # Nama file bukti foto yang diupload (nullable, maks 5 MB, JPEG/PNG/WEBP)
    foto_bukti = Column(String(255), nullable=True)
