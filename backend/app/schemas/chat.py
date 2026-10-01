from pydantic import BaseModel, Field
from datetime import datetime

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, description="Pertanyaan warga (1-500 karakter)")

class ChatResponse(BaseModel):
    id: int
    user_id: int
    prompt: str
    response: str
    timestamp: datetime

    class Config:
        from_attributes = True
