import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.domains.attendance.models import Attendance

def calculate_no_show_risk(db: Session, patient_id: uuid.UUID) -> dict:
    """
    Calculates the no-show risk percentage based on historical attendance.
    Risk = (Missed Appointments / Total Appointments) * 100
    """
    # 1. Get total appointments recorded for this patient
    total_query = select(func.count(Attendance.id)).where(
        Attendance.patient_id == patient_id
    )
    total_records = db.execute(total_query).scalar() or 0

    # Edge Case: New patient with no history
    if total_records == 0:
        return {
            "patient_id": patient_id,
            "total_records": 0,
            "missed_appointments": 0,
            "risk_percentage": 0.0,
            "risk_level": "LOW (New Patient)"
        }

    # 2. Get missed appointments
    missed_query = select(func.count(Attendance.id)).where(
        Attendance.patient_id == patient_id,
        Attendance.was_present == False
    )
    missed_records = db.execute(missed_query).scalar() or 0

    # 3. Calculate Risk
    risk_percentage = (missed_records / total_records) * 100.0
    
    # Classify risk
    risk_level = "LOW"
    if risk_percentage >= 50.0:
        risk_level = "HIGH"
    elif risk_percentage >= 25.0:
        risk_level = "MEDIUM"

    return {
        "patient_id": patient_id,
        "total_records": total_records,
        "missed_appointments": missed_records,
        "risk_percentage": round(risk_percentage, 2),
        "risk_level": risk_level
    }