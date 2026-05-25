from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Doctor, User, DoctorAvailability, AuditAction
from app.schemas.schemas import (
    DoctorOut, DoctorUpdate, DoctorAvailabilityCreate, DoctorAvailabilityOut,
    AvailableSlot, PaginatedResponse, DoctorCreate
)
from app.core.security import get_current_user, require_admin, require_doctor
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.db.cache import cache

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=PaginatedResponse)
async def list_doctors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    specialty: Optional[str] = None,
    available_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Doctor)
        .options(selectinload(Doctor.user))
        .where(Doctor.hospital_id == current_user.hospital_id)
    )
    if available_only:
        query = query.where(Doctor.is_available == True)
    if specialty:
        query = query.where(Doctor.specialty == specialty)
    if search:
        s = f"%{search}%"
        query = query.join(User, Doctor.user_id == User.id).where(
            or_(User.first_name.ilike(s), User.last_name.ilike(s))
        )
    count_q = select(func.count()).select_from(
        select(Doctor).where(Doctor.hospital_id == current_user.hospital_id).subquery()
    )
    total = (await db.execute(count_q)).scalar_one()
    query = query.offset((page - 1) * page_size).limit(page_size)
    doctors = (await db.execute(query)).scalars().all()
    return PaginatedResponse(
        items=[DoctorOut.model_validate(d).model_dump() for d in doctors],
        total=total, page=page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(
    doctor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Doctor).options(selectinload(Doctor.user))
        .where(and_(Doctor.id == doctor_id, Doctor.hospital_id == current_user.hospital_id))
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Doctor not found")
    return doc


@router.patch("/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Doctor).options(selectinload(Doctor.user))
        .where(and_(Doctor.id == doctor_id, Doctor.hospital_id == current_user.hospital_id))
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Doctor not found")
    # Only admins or the doctor themselves
    if current_user.role.value not in ("admin", "super_admin") and doc.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")
    old = data.model_dump(exclude_unset=True)
    for k, v in old.items():
        setattr(doc, k, v)
    await db.flush()
    await db.refresh(doc)
    await cache.delete_pattern(f"doctor:{doctor_id}:*")
    await AuditService.log(db, AuditAction.update, "doctor", doctor_id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id,
                           new_values=old, ip_address=request.client.host if request.client else None)
    return doc


@router.get("/{doctor_id}/slots", response_model=List[AvailableSlot])
async def get_slots(
    doctor_id: int,
    date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AppointmentService.get_available_slots(db, doctor_id, date)


@router.get("/{doctor_id}/availability", response_model=List[DoctorAvailabilityOut])
async def get_availability(
    doctor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DoctorAvailability)
        .where(and_(DoctorAvailability.doctor_id == doctor_id, DoctorAvailability.is_active == True))
        .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
    )
    return result.scalars().all()


@router.post("/{doctor_id}/availability", response_model=DoctorAvailabilityOut, status_code=201)
async def set_availability(
    doctor_id: int,
    data: DoctorAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Doctor, doctor_id)
    if not doc or doc.hospital_id != current_user.hospital_id:
        raise HTTPException(404, "Doctor not found")
    if current_user.role.value not in ("admin", "super_admin") and doc.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")
    avail = DoctorAvailability(doctor_id=doctor_id, **data.model_dump())
    db.add(avail)
    await db.flush()
    await db.refresh(avail)
    return avail


@router.post("/self", response_model=DoctorOut, status_code=201)
async def create_doctor_profile(
    data: "DoctorCreate",
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    from app.schemas.schemas import DoctorCreate
    existing = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Doctor profile already exists")
    doc = Doctor(hospital_id=current_user.hospital_id, user_id=current_user.id, **data.model_dump())
    db.add(doc)
    await db.flush()
    result = await db.execute(
        select(Doctor).options(selectinload(Doctor.user)).where(Doctor.id == doc.id)
    )
    return result.scalar_one()
