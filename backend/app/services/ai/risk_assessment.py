from typing import List, Dict, Any, Optional
from app.schemas.risk import RiskAssessment, RiskAssessmentResponse
from datetime import datetime

# Level-aware recommendations: the advice should match how high the risk is,
# instead of a single generic line ("consult a doctor if HIGH") shown even when
# the score already IS high.
_RECOMMENDATIONS = {
    "Type 2 Diabetes": {
        "HIGH": "Your glucose markers indicate a high diabetes risk. Please see a doctor promptly to confirm and start a management plan. In the meantime, follow a low-glycemic diet, cut added sugar, and stay active.",
        "MODERATE": "Your glucose markers are borderline (pre-diabetes range). Discuss with your doctor, reduce refined carbs and sugar, increase physical activity, and recheck your levels in a few months.",
        "LOW": "Your glucose markers look healthy. Maintain a balanced, low-glycemic diet and regular exercise to keep them that way.",
    },
    "Cardiovascular Disease": {
        "HIGH": "Your lipid profile indicates a high cardiovascular risk. Please consult a doctor about lipid management (statin therapy may be considered). Prioritize a heart-healthy diet, regular aerobic exercise, and avoid tobacco.",
        "MODERATE": "Some lipid values are borderline. Improve your diet (less saturated/trans fat), exercise regularly, and recheck your lipid panel; discuss the results with your doctor.",
        "LOW": "Your lipid profile is within healthy ranges. Keep up regular aerobic exercise and a heart-healthy diet.",
    },
}


def _find(lab_data, *includes, exclude=()):
    for i in lab_data:
        name = i["test_name"].lower()
        if all(k in name for k in includes) and not any(x in name for x in exclude):
            return i
    return None


def _num(item) -> Optional[float]:
    if not item:
        return None
    try:
        return float(item["value"])
    except (ValueError, TypeError, KeyError):
        return None


def calculate_diabetes_risk(lab_data: List[Dict[str, Any]]) -> RiskAssessment:
    """Diabetes risk from Glucose + HbA1c."""
    score = 0.0
    factors = []

    glucose = _find(lab_data, "glucose")
    g = _num(glucose)
    if g is not None:
        if g > 126:
            score += 0.6
            factors.append(f"High Fasting Glucose ({g} {glucose.get('unit', '')})".strip())
        elif g > 100:
            score += 0.3
            factors.append(f"Borderline Glucose ({g} {glucose.get('unit', '')})".strip())

    hba1c = _find(lab_data, "hba1c")
    h = _num(hba1c)
    if h is not None:
        if h > 6.5:
            score += 0.8
            factors.append(f"Critical HbA1c Level ({h}%)")
        elif h > 5.7:
            score += 0.4
            factors.append(f"Pre-diabetic HbA1c Level ({h}%)")

    score = min(score, 1.0)
    level = "HIGH" if score > 0.7 else "MODERATE" if score > 0.3 else "LOW"
    return RiskAssessment(
        condition="Type 2 Diabetes",
        risk_level=level,
        score=score,
        contributing_factors=factors if factors else ["No significant markers found"],
        recommendation=_RECOMMENDATIONS["Type 2 Diabetes"][level],
    )


def calculate_cvd_risk(lab_data: List[Dict[str, Any]]) -> RiskAssessment:
    """Cardiovascular risk from the full lipid profile (LDL, HDL, Total, Triglycerides)."""
    score = 0.0
    factors = []

    ldl = _num(_find(lab_data, "ldl"))
    if ldl is not None and ldl > 160:
        score += 0.5
        factors.append(f"High LDL Cholesterol ({ldl})")

    hdl = _num(_find(lab_data, "hdl", exclude=("vldl",)))
    if hdl is not None and hdl < 40:
        score += 0.3
        factors.append(f"Low HDL 'Good' Cholesterol ({hdl})")

    chol = _num(_find(lab_data, "cholesterol", exclude=("ldl", "hdl", "non")))
    if chol is not None and chol > 240:
        score += 0.4
        factors.append(f"High Total Cholesterol ({chol})")

    # Triglycerides were previously ignored entirely — a real CVD/metabolic factor.
    trig = _num(_find(lab_data, "triglyceride"))
    if trig is not None:
        if trig > 200:
            score += 0.3
            factors.append(f"High Triglycerides ({trig})")
        elif trig > 150:
            score += 0.15
            factors.append(f"Borderline Triglycerides ({trig})")

    score = min(score, 1.0)
    level = "HIGH" if score > 0.6 else "MODERATE" if score > 0.3 else "LOW"
    return RiskAssessment(
        condition="Cardiovascular Disease",
        risk_level=level,
        score=round(score, 2),
        contributing_factors=factors if factors else ["Lipid profile within normal ranges"],
        recommendation=_RECOMMENDATIONS["Cardiovascular Disease"][level],
    )

def perform_full_risk_assessment(lab_data: List[Dict[str, Any]]) -> RiskAssessmentResponse:
    if not lab_data:
        return RiskAssessmentResponse(
            overall_status="INSUFFICIENT_DATA",
            assessments=[],
            last_updated=datetime.now().isoformat()
        )
        
    assessments = [
        calculate_diabetes_risk(lab_data),
        calculate_cvd_risk(lab_data)
    ]
    
    # Determine overall status
    high_risks = [a for a in assessments if a.risk_level == "HIGH"]
    if high_risks:
        status = "CRITICAL"
    elif any(a for a in assessments if a.risk_level == "MODERATE"):
        status = "ATTENTION_REQUIRED"
    else:
        status = "HEALTHY"
        
    return RiskAssessmentResponse(
        overall_status=status,
        assessments=assessments,
        last_updated=datetime.now().isoformat()
    )
