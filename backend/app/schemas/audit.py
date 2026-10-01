from pydantic import BaseModel
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: int
    report_id: int
    admin_id: int
    status_baru: str
    timestamp: datetime

    class Config:
        from_attributes = True
