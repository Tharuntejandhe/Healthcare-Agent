from pydantic import BaseModel
from typing import List, Optional

class RiskAssessment(BaseModel):
    condition: str
    risk_level: str  # LOW, MODERATE, HIGH
    score: float     # 0.0 to 1.0
    contributing_factors: List[str]
    recommendation: str

class RiskAssessmentResponse(BaseModel):
    overall_status: str
    assessments: List[RiskAssessment]
    last_updated: str
