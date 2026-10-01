from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.crud.chat import create_chat_entry, get_user_chat_history
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def ask_chatbot(
    chat_in: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_chat_entry(db, user_id=current_user.id, prompt=chat_in.prompt)

@router.get("/history", response_model=List[ChatResponse])
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_chat_history(db, user_id=current_user.id, limit=limit)
