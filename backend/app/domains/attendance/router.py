import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.domains.attendance.models import Attendance
from app.domains.attendance.schemas import AttendanceCreate, AttendanceResponse, RiskProfileResponse
from app.domains.attendance.services import calculate_no_show_risk

router = APIRouter(prefix="/attendance", tags=["Attendance & Prediction"])

@router.post("/record", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def record_attendance(attendance_in: AttendanceCreate, db: Session = Depends(get_db)):
    """Record whether a patient showed up for an appointment."""
    new_record = Attendance(
        patient_id=attendance_in.patient_id,
        appointment_id=attendance_in.appointment_id,
        was_present=attendance_in.was_present
    )
    
    db.add(new_record)
    try:
        db.commit()
        db.refresh(new_record)
        return new_record
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance for this appointment has already been recorded."
        )

@router.get("/patients/{patient_id}/no-show-risk", response_model=RiskProfileResponse)
def get_patient_no_show_risk(patient_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get the heuristic no-show risk prediction for a patient."""
    risk_profile = calculate_no_show_risk(db, patient_id)
    return risk_profile