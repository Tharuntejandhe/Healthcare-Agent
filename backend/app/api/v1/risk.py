import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.risk import RiskAssessmentResponse
from app.services.audit import record_event
from app.services.ai.parser import parse_lab_report_lines
from app.services.ai.rag import get_all_documents
from app.services.ai.risk_assessment import perform_full_risk_assessment

logger = logging.getLogger("app.api.risk")
router = APIRouter()


@router.get("/my-risk", response_model=RiskAssessmentResponse)
async def get_user_risk_assessment(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Analyze all uploaded medical documents to assess disease risks."""

    def _assess() -> RiskAssessmentResponse:
        raw_text = get_all_documents(user_id=current_user.id)
        if not raw_text or "No patient reports" in raw_text:
            return RiskAssessmentResponse(overall_status="NO_DATA", assessments=[], last_updated="")
        lab_data = parse_lab_report_lines(raw_text.split("\n")[:100])
        return perform_full_risk_assessment(lab_data)

    try:
        result = await run_in_threadpool(_assess)
        record_event(
            db, action="risk.assess", resource_type="risk",
            user_id=current_user.id, request=request,
        )
        return result
    except Exception:
        logger.exception("risk assessment failed (user=%s)", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="Risk assessment is temporarily unavailable. Please try again in a moment.",
        )
