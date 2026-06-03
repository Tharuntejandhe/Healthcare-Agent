from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.chat import ChatSession, ChatMessage

def get_sessions_for_user(db: Session, user_id: str) -> List[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(desc(ChatSession.updated_at)).all()

def get_session(db: Session, session_id: str, user_id: str) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()

def create_session(db: Session, session_id: str, user_id: str, title: str) -> ChatSession:
    db_session = ChatSession(id=session_id, user_id=user_id, title=title)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_session_title(db: Session, session_id: str, user_id: str, title: str) -> Optional[ChatSession]:
    db_session = get_session(db, session_id, user_id)
    if db_session:
        db_session.title = title
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_session(db: Session, session_id: str, user_id: str) -> bool:
    db_session = get_session(db, session_id, user_id)
    if db_session:
        db.delete(db_session)
        db.commit()
        return True
    return False

def add_message(db: Session, session_id: str, id: str, role: str, content: str, attachments: Optional[list] = None) -> ChatMessage:
    db_msg = ChatMessage(
        id=id,
        session_id=session_id,
        role=role,
        content=content,
        attachments=attachments or []
    )
    db.add(db_msg)
    
    # Update session updated_at
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        # SQLAlchemy handles onupdate automatically, but we can force it
        db_session.updated_at = db_session.updated_at
    
    db.commit()
    db.refresh(db_msg)
    return db_msg
