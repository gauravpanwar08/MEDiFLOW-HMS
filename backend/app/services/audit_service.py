from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.models import AuditLog, AuditAction


class AuditService:

    @staticmethod
    async def log(
        db: AsyncSession,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        hospital_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            hospital_id=hospital_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            notes=notes,
        )
        db.add(entry)
        await db.flush()
        return entry

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        hospital_id: int,
        page: int = 1,
        page_size: int = 50,
        resource_type: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[List[AuditLog], int]:
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.hospital_id == hospital_id)
            .order_by(AuditLog.created_at.desc())
        )
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)

        total = (await db.execute(
            select(func.count()).select_from(
                select(AuditLog).where(AuditLog.hospital_id == hospital_id).subquery()
            )
        )).scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return result.scalars().all(), total
