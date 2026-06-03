from app.db.base_class import Base

# Import all models here so that Base.metadata has them
from app.models.user import User
from app.models.token import RevokedToken
from app.models.audit import AuditLog
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage