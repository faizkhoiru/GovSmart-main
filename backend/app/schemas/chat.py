from pydantic import BaseModel, Field, Extra
from typing import List, Optional, Any
from datetime import datetime

class ChatRequest(BaseModel):
    pertanyaan: Optional[str] = Field(None, min_length=1, max_length=500)
    prompt: Optional[str] = Field(None, min_length=1, max_length=500)

    model_config = {"extra": "ignore"}

    def get_query(self) -> str:
        return (self.pertanyaan or self.prompt or "").strip()

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

