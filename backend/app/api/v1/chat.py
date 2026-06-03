import logging
from typing import Any

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

logger = logging.getLogger("app.api.chat")
router = APIRouter()


class ChatRequest(BaseModel):
    # Generous cap: when the user attaches photos, the vision analyses are
    # prepended to the query, so 4000 chars was too small (caused 422s). The
    # chat model has a large context window; clamp only to bound abuse.
    query: str = Field(min_length=1, max_length=32000)
    use_personal_analysis: bool = False


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
    return {"response": response_text, "classification": classification}
