from pydantic import BaseModel, Field, Extra
from typing import List, Optional, Any
from datetime import datetime

class ChatRequest(BaseModel, extra=Extra.forbid):
    pertanyaan: str = Field(..., min_length=1, max_length=500)

class Sumber(BaseModel):
    no: Optional[int]
    judul: Optional[str]
    konteks: Optional[str]
    layanan: Optional[str]
    halaman: Optional[str]

class ChatResponse(BaseModel):
    jawaban: str
    intent: Optional[str]
    mode: Optional[str]
    sumber: Optional[List[Sumber]]

class ChatHistoryItem(BaseModel):
    prompt: str
    response: str
    timestamp: Any

class ChatHistoryOut(BaseModel):
    results: List[ChatHistoryItem]
    count: int

