from sqlalchemy.orm import Session
from app.models.chat import ChatHistory
from app.core.ai_routing import generate_ai_chatbot_response

def create_chat_entry(db: Session, user_id: int, prompt: str):
    response_text = generate_ai_chatbot_response(prompt)
    chat_entry = ChatHistory(
        user_id=user_id,
        prompt=prompt,
        response=response_text
    )
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)
    return chat_entry

def get_user_chat_history(db: Session, user_id: int, limit: int = 50):
    return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
