from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuditLogResponse(BaseModel):
    id: int
    report_id: int
    admin_id: Optional[int] = None
    status_baru: str
    timestamp: datetime

    class Config:
        from_attributes = True
