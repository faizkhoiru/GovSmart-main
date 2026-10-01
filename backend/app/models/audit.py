# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status_baru = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
