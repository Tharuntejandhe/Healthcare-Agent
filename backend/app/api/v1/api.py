from fastapi import APIRouter
from app.api.v1 import auth, chat, documents, risk, users, vision, speech

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(vision.router, prefix="/vision", tags=["vision"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
