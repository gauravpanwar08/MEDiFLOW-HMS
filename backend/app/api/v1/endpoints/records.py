import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.db.session import get_db
from app.models.models import Patient, MedicalRecord, User, AuditAction
from app.schemas.schemas import MedicalRecordOut, PaginatedResponse
from app.core.security import get_current_user, require_doctor
from app.core.config import settings
from app.services.audit_service import AuditService

router = APIRouter(prefix="/records", tags=["Medical Records"])

UPLOAD_BASE = Path(settings.UPLOAD_DIR)
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


async def get_patient_or_403(db, patient_id, current_user):
    result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.hospital_id == current_user.hospital_id))
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Patient not found")
    if current_user.role.value == "patient" and p.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return p


@router.post("/patients/{patient_id}/upload", response_model=MedicalRecordOut, status_code=201)
async def upload_record(
    patient_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    record_type: str = Query("report"),
    appointment_id: Optional[int] = Query(None),
    is_confidential: bool = Query(False),
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    await get_patient_or_403(db, patient_id, current_user)
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f"Unsupported type: {file.content_type}")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

    dest = UPLOAD_BASE / f"h{current_user.hospital_id}" / f"p{patient_id}"
    dest.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{ext}"
    filepath = dest / filename
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    rec = MedicalRecord(
        hospital_id=current_user.hospital_id,
        patient_id=patient_id,
        uploaded_by_id=current_user.id,
        appointment_id=appointment_id,
        file_name=file.filename,
        file_path=str(filepath),
        file_type=file.content_type,
        file_size=len(content),
        title=title or file.filename,
        description=description,
        record_type=record_type,
        is_confidential=is_confidential,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    await AuditService.log(db, AuditAction.create, "medical_record", rec.id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id,
                           new_values={"patient_id": patient_id, "file": file.filename})
    return rec


@router.get("/patients/{patient_id}", response_model=PaginatedResponse)
async def list_records(
    patient_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    record_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_patient_or_403(db, patient_id, current_user)
    query = select(MedicalRecord).where(
        and_(MedicalRecord.patient_id == patient_id, MedicalRecord.hospital_id == current_user.hospital_id)
    )
    if current_user.role.value not in ("admin", "super_admin", "doctor"):
        query = query.where(MedicalRecord.is_confidential == False)
    if record_type:
        query = query.where(MedicalRecord.record_type == record_type)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    query = query.order_by(MedicalRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    records = (await db.execute(query)).scalars().all()
    return PaginatedResponse(
        items=[MedicalRecordOut.model_validate(r).model_dump() for r in records],
        total=total, page=page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{record_id}/download")
async def download_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MedicalRecord).where(
            and_(MedicalRecord.id == record_id, MedicalRecord.hospital_id == current_user.hospital_id)
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Record not found")
    if current_user.role.value == "patient":
        pat = (await db.execute(select(Patient).where(Patient.user_id == current_user.id))).scalar_one_or_none()
        if not pat or rec.patient_id != pat.id:
            raise HTTPException(403, "Access denied")
        if rec.is_confidential:
            raise HTTPException(403, "Confidential — requires doctor access")
    if not os.path.exists(rec.file_path):
        raise HTTPException(404, "File not found on server")
    await AuditService.log(db, AuditAction.access, "medical_record", record_id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id)
    return FileResponse(path=rec.file_path, filename=rec.file_name, media_type=rec.file_type)


@router.delete("/{record_id}", status_code=204)
async def delete_record(
    record_id: int,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MedicalRecord).where(
            and_(MedicalRecord.id == record_id, MedicalRecord.hospital_id == current_user.hospital_id)
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Record not found")
    if os.path.exists(rec.file_path):
        os.remove(rec.file_path)
    await AuditService.log(db, AuditAction.delete, "medical_record", record_id,
                           user_id=current_user.id, hospital_id=current_user.hospital_id)
    await db.delete(rec)
