import logging
import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from app.api import deps
from app.core.limits import AI_LIMIT, limiter
from app.models.user import User
from app.services.audit import record_event
from app.services.ai.disclaimer import ensure_disclaimer
from app.services.ai.graph import ai_app
from app.crud import crud_chat

logger = logging.getLogger("app.api.chat")
router = APIRouter()


class ChatRequest(BaseModel):
    # Generous cap: when the user attaches photos, the vision analyses are
    # prepended to the query, so 4000 chars was too small (caused 422s). The
    # chat model has a large context window; clamp only to bound abuse.
    query: str = Field(min_length=1, max_length=32000)
    use_personal_analysis: bool = False
    session_id: Optional[str] = None
    attachments: Optional[list] = None

class SessionCreate(BaseModel):
    id: str
    title: str

class SessionUpdate(BaseModel):
    title: str


class ChatResponse(BaseModel):
    response: str
    classification: str


@router.post("/query", response_model=ChatResponse)
@limiter.limit(AI_LIMIT)
async def handle_chat_query(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Send a query to the AI Healthcare Orchestrator.

    The LangGraph invocation fans out to several blocking Groq round-trips, so it
    runs in a worker thread to avoid stalling the event loop for all users.
    """

    if body.session_id:
        crud_chat.add_message(
            db=db,
            session_id=body.session_id,
            id=str(uuid.uuid4()),
            role="user",
            content=body.query,
            attachments=body.attachments
        )

    def _run() -> dict:
        from app.services.ai.parser import parse_lab_report_lines
        from app.services.ai.rag import get_all_documents
        from app.services.analytical_report import generate_health_summary

        messages = []
        if body.use_personal_analysis:
            profile_context = (
                f"User Profile: Name: {current_user.full_name}, Email: {current_user.email}."
            )
            raw_docs = get_all_documents(user_id=current_user.id)
            if "No patient reports" not in raw_docs:
                data = parse_lab_report_lines(raw_docs.split("\n")[:50])
                medical_summary = generate_health_summary(data)
                messages.append(
                    SystemMessage(
                        content=(
                            f"{profile_context}\n\nClinical Summary from all Reports:\n{medical_summary}"
                            "\n\nPlease use this information to provide personalized advice."
                        )
                    )
                )
            else:
                messages.append(
                    SystemMessage(content=f"{profile_context}\nNote: No medical reports found for this user yet.")
                )

        messages.append(HumanMessage(content=body.query))
        initial_state = {"messages": messages, "user_id": current_user.id}
        config = {"configurable": {"thread_id": str(current_user.id)}}
        return ai_app.invoke(initial_state, config=config)

    try:
        result = await run_in_threadpool(_run)
    except Exception:
        logger.exception("chat query failed (user=%s)", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again in a moment.",
        )

    classification = result.get("classification", "unknown")
    record_event(
        db, action="chat.query", resource_type="chat",
        user_id=current_user.id, request=request, detail=classification,
    )

    # Every AI health response must carry a safety disclaimer.
    response_text = ensure_disclaimer(
        result.get("final_response", "Sorry, I could not process that request.")
    )

    if body.session_id:
        crud_chat.add_message(
            db=db,
            session_id=body.session_id,
            id=str(uuid.uuid4()),
            role="ai",
            content=response_text
        )

    return {"response": response_text, "classification": classification}

@router.get("/sessions")
def list_sessions(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user)):
    sessions = crud_chat.get_sessions_for_user(db, current_user.id)
    return [{"id": s.id, "title": s.title, "updatedAt": s.updated_at.isoformat()} for s in sessions]

@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user)):
    session = crud_chat.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = [{"id": m.id, "role": m.role, "content": m.content, "attachments": m.attachments or []} for m in session.messages]
    return {"id": session.id, "title": session.title, "updatedAt": session.updated_at.isoformat(), "messages": messages}

@router.post("/sessions")
def create_session(body: SessionCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user)):
    session = crud_chat.create_session(db, body.id, current_user.id, body.title)
    return {"id": session.id, "title": session.title, "updatedAt": session.updated_at.isoformat()}

@router.put("/sessions/{session_id}")
def update_session(session_id: str, body: SessionUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user)):
    session = crud_chat.update_session_title(db, session_id, current_user.id, body.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": session.id, "title": session.title, "updatedAt": session.updated_at.isoformat()}

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user)):
    if crud_chat.delete_session(db, session_id, current_user.id):
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Session not found")
