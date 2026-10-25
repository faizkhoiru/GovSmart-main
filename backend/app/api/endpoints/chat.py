# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Request, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.privacy import mask_pii
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryOut
# pyrefly: ignore [missing-import]
import httpx
import time
from collections import defaultdict
from app.crud import chat as crud_chat

router = APIRouter()

RATE_LIMIT = getattr(settings, "CHAT_RATE_LIMIT_PER_MINUTE", 20)
WINDOW = 60
rl_state = defaultdict(list)

async def limited_user(user_id):
    now = time.time()
    window_start = now - WINDOW
    hits = rl_state[user_id]
    rl_state[user_id] = [t for t in hits if t > window_start]
    if RATE_LIMIT > 0 and len(rl_state[user_id]) >= RATE_LIMIT:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"kode": "RATE_LIMITED", "pesan": f"Maks {RATE_LIMIT}/menit", "fields": [], "retry_after": WINDOW},
        )
    rl_state[user_id].append(now)

@router.post("/", response_model=ChatResponse, status_code=200)
async def ask_chatbot(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    user_id = current_user.id
    await limited_user(user_id)
    pertanyaan = mask_pii(payload.get_query())
    if not (1 <= len(pertanyaan) <= 500):
        raise HTTPException(422, detail="Pertanyaan wajib 1-500 karakter.")
    db.rollback()  # kunci: rolling sesi supaya pool DB tidak hold selama await
    chat_url = settings.CHATBOT_URL+"/ask"
    headers = {"X-Internal-Token": settings.CHATBOT_INTERNAL_TOKEN}
    timeout = getattr(settings, "CHATBOT_TIMEOUT", 180)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(chat_url, json={"pertanyaan":pertanyaan}, headers=headers)
        except httpx.TimeoutException:
            raise HTTPException(504, detail={"kode":"CHATBOT_TIMEOUT","pesan":"Chatbot membutuhkan waktu lebih lama untuk memproses jawaban. Silakan coba sesaat lagi.","fields":[]})
        except httpx.RequestError as exc:
            import logging
            logging.getLogger(__name__).error(f"Chatbot connection error: {exc}")
            raise HTTPException(503, detail={"kode":"CHATBOT_UNAVAILABLE","pesan":"Chatbot layanan tidak tersedia.","fields":[]})
    if resp.status_code == 401:
        raise HTTPException(503, detail={"kode":"CHATBOT_UNAVAILABLE","pesan":"Layanan chatbot gagal autentikasi.","fields":[]})
    if resp.status_code == 429:
        raise HTTPException(429, detail={"kode":"CHATBOT_BUSY","pesan":"Chatbot sedang sibuk.","fields":[],"retry_after":5})
    if resp.status_code == 422:
        raise HTTPException(422, detail=resp.json())
    if resp.status_code != 200:
        raise HTTPException(503, detail={"kode":"CHATBOT_UNAVAILABLE","pesan":"Gagal komunikasi dengan chatbot.","fields":[]})
    body = resp.json()
    jawaban = mask_pii(body.get("jawaban",""))[:2000]
    crud_chat.create(db, user_id=user_id, prompt=pertanyaan, response=jawaban)
    chat_res = {k:body[k] for k in ("jawaban","intent","mode") if k in body}
    if "sumber" in body:
        chat_res["sumber"] = [
            {k:v for k,v in sumber.items() if k in ["no","judul","konteks","layanan","halaman"]}
            for sumber in body["sumber"]
        ]
    return chat_res

@router.get("/history", response_model=ChatHistoryOut)
def chat_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    limit = min(100, max(1, limit))
    rows = crud_chat.history(db, user_id=current_user.id, limit=limit, offset=offset)
    return {"results": rows, "count": len(rows)}

@router.delete("/history", status_code=204)
def chat_clear_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    crud_chat.clear_history(db, user_id=current_user.id)
    return None

