from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.domains.appointments.models import Appointment
from app.domains.appointments.schemas import AppointmentCreate, AppointmentResponse

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment_in: AppointmentCreate, db: Session = Depends(get_db)):
    new_appointment = Appointment(
        patient_id=appointment_in.patient_id,
        doctor_id=appointment_in.doctor_id,
        appointment_time=appointment_in.appointment_time,
        priority=appointment_in.priority
    )
    
    db.add(new_appointment)
    try:
        db.commit()
        db.refresh(new_appointment)
        return new_appointment
    except IntegrityError:
        db.rollback()
        # This catches our UniqueConstraint natively without race conditions
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Double booking detected: This doctor already has an appointment scheduled at this exact time."
        )

@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # SQLAlchemy 2.0 select syntax
    appointments = db.execute(
        select(Appointment).offset(skip).limit(limit)
    ).scalars().all()
    
    return appointments