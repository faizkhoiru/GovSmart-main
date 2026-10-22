from sqlalchemy.orm import Session
from app.models.chat import ChatHistory
from datetime import datetime

def create(db:Session, user_id:int, prompt:str, response:str):
    row = ChatHistory(user_id=user_id, prompt=prompt, response=response, timestamp=datetime.utcnow())
    db.add(row)
    db.commit()
    return row

def history(db:Session, user_id:int, limit:int, offset:int):
    q = db.query(ChatHistory).filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).offset(offset).limit(limit)
    return [
        {"prompt": r.prompt, "response": r.response, "timestamp": r.timestamp} for r in q.all()
    ]

