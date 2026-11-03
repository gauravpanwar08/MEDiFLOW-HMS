from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from app.models.models import User, Hospital, UserRole
from app.schemas.schemas import UserCreate
from app.core.security import get_password_hash


class UserService:

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str, hospital_id: int) -> Optional[User]:
        clean_email = email.strip().lower()
        result = await db.execute(
            select(User).where(and_(func.lower(User.email) == clean_email, User.hospital_id == hospital_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: UserCreate, hospital: Hospital, role: Optional[UserRole] = None) -> User:
        from app.models.models import Patient
        assigned_role = role or data.role
        clean_email = data.email.strip().lower()
        user = User(
            email=clean_email,
            hashed_password=get_password_hash(data.password),
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            role=assigned_role,
            phone=data.phone.strip() if data.phone else None,
            hospital_id=hospital.id,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        if assigned_role == UserRole.patient:
            pat_result = await db.execute(select(Patient).where(Patient.user_id == user.id))
            if not pat_result.scalar_one_or_none():
                patient = Patient(
                    hospital_id=hospital.id,
                    user_id=user.id,
                    emergency_contact_phone=user.phone,
                )
                db.add(patient)
                await db.flush()

        return user

    @staticmethod
    async def list_users(
        db: AsyncSession,
        hospital_id: int,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> Tuple[List[User], int]:
        query = select(User).where(User.hospital_id == hospital_id)
        if role:
            query = query.where(User.role == role)
        if search:
            s = f"%{search}%"
            query = query.where(or_(
                User.email.ilike(s),
                User.first_name.ilike(s),
                User.last_name.ilike(s),
            ))
        total = (await db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar_one()
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return result.scalars().all(), total
