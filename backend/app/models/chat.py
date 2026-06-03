from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String, nullable=False, default="New Consultation")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String, nullable=False) # 'user' or 'ai'
    content = Column(Text, nullable=False)
    agent_name = Column(String, nullable=True)
    image_urls = Column(JSON, nullable=True) # deprecated, keeping for backwards compat
    attachments = Column(JSON, nullable=True) # {name: str, type: str, url: str}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
