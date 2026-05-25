from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Patient, User, AuditAction
from app.schemas.schemas import PatientCreate, PatientOut, PatientUpdate, PaginatedResponse
from app.core.security import get_current_user, require_doctor
from app.services.audit_service import AuditService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=PaginatedResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    blood_group: Optional[str] = None,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Patient).options(selectinload(Patient.user))
        .where(Patient.hospital_id == current_user.hospital_id)
    )
    if blood_group:
        query = query.where(Patient.blood_group == blood_group)
    if search:
        s = f"%{search}%"
        query = query.join(User, Patient.user_id == User.id).where(
            or_(User.first_name.ilike(s), User.last_name.ilike(s), User.email.ilike(s))
        )
    count_q = select(func.count()).select_from(
        select(Patient).where(Patient.hospital_id == current_user.hospital_id).subquery()
    )
    total = (await db.execute(count_q)).scalar_one()
    query = query.offset((page - 1) * page_size).limit(page_size)
    patients = (await db.execute(query)).scalars().all()
    return PaginatedResponse(
        items=[PatientOut.model_validate(p).model_dump() for p in patients],
        total=total, page=page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/me", response_model=PatientOut)
async def get_my_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Patient).options(selectinload(Patient.user)).where(Patient.user_id == current_user.id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Patient profile not found. Create one first.")
    return p


@router.post("/me", response_model=PatientOut, status_code=201)
async def create_my_profile(
    data: PatientCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Patient profile already exists")
    patient = Patient(hospital_id=current_user.hospital_id, user_id=current_user.id, **data.model_dump())
    db.add(patient)
    await db.flush()
    await AuditService.log(db, AuditAction.create, "patient", patient.id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id,
                           ip_address=request.client.host if request.client else None)
    result = await db.execute(
        select(Patient).options(selectinload(Patient.user)).where(Patient.id == patient.id)
    )
    return result.scalar_one()


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: int,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Patient).options(selectinload(Patient.user))
        .where(and_(Patient.id == patient_id, Patient.hospital_id == current_user.hospital_id))
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Patient not found")
    return p


@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Patient).options(selectinload(Patient.user))
        .where(and_(Patient.id == patient_id, Patient.hospital_id == current_user.hospital_id))
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Patient not found")
    if current_user.role.value not in ("admin", "super_admin", "doctor") and p.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(p, k, v)
    await db.flush()
    await db.refresh(p)
    await AuditService.log(db, AuditAction.update, "patient", patient_id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id,
                           new_values=updates, ip_address=request.client.host if request.client else None)
    return p
