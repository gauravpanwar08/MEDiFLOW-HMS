from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Patient, Doctor, Appointment, AppointmentStatus, AppointmentPriority, User, AuditAction
from app.schemas.schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate, PaginatedResponse
from app.core.security import get_current_user, require_doctor
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=PaginatedResponse)
async def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.schemas.schemas import PaginationParams
    # Patients see only their own; doctors see theirs; admins see all
    my_patient_id = None
    my_doctor_id = None
    if current_user.role.value == "patient":
        pat = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
        pat_obj = pat.scalar_one_or_none()
        if pat_obj:
            my_patient_id = pat_obj.id
    elif current_user.role.value == "doctor":
        doc = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doc_obj = doc.scalar_one_or_none()
        if doc_obj:
            my_doctor_id = doc_obj.id

    params = PaginationParams(page=page, page_size=page_size)
    appts, total = await AppointmentService.list_appointments(
        db=db,
        hospital_id=current_user.hospital_id,
        params=params,
        doctor_id=my_doctor_id or doctor_id,
        patient_id=my_patient_id or patient_id,
        status=AppointmentStatus(status) if status else None,
        priority=AppointmentPriority(priority) if priority else None,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedResponse(
        items=[AppointmentOut.model_validate(a).model_dump() for a in appts],
        total=total, page=page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.post("", response_model=AppointmentOut, status_code=201)
async def book_appointment(
    data: AppointmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get patient id — patients use their own profile; admins/doctors must pass patient_id separately
    if current_user.role.value == "patient":
        pat = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
        pat_obj = pat.scalar_one_or_none()
        if not pat_obj:
            raise HTTPException(400, "Complete your patient profile before booking")
        patient_id = pat_obj.id
    elif hasattr(data, 'patient_id') and data.patient_id:
        patient_id = data.patient_id
    else:
        raise HTTPException(400, "patient_id is required for non-patient users")

    appt = await AppointmentService.create(db, current_user.hospital_id, patient_id, data)
    await AuditService.log(db, AuditAction.create, "appointment", appt.id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id,
                           new_values={"doctor_id": data.doctor_id, "date": str(data.appointment_date)},
                           ip_address=request.client.host if request.client else None)
    return await AppointmentService.get_by_id(db, appt.id, current_user.hospital_id)


@router.get("/{appt_id}", response_model=AppointmentOut)
async def get_appointment(
    appt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appt = await AppointmentService.get_by_id(db, appt_id, current_user.hospital_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")
    return appt


@router.patch("/{appt_id}", response_model=AppointmentOut)
async def update_appointment(
    appt_id: int,
    data: AppointmentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appt = await AppointmentService.get_by_id(db, appt_id, current_user.hospital_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")
    updated = await AppointmentService.update(db, appt, data, current_user.id)
    await AuditService.log(db, AuditAction.update, "appointment", appt_id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id,
                           new_values=data.model_dump(exclude_unset=True),
                           ip_address=request.client.host if request.client else None)
    return updated
