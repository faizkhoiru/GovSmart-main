from sqlalchemy import Column, Integer, String
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    nama_dinas = Column(String(100), unique=True, nullable=False)
