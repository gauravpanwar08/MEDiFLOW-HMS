import uuid
from enum import Enum as PyEnum
import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, Enum as SQLEnum, Uuid, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

# 1. TYPE_CHECKING prevents runtime circular imports while satisfying the IDE
if TYPE_CHECKING:
    from app.domains.patients.models import Patient
    from app.domains.doctors.models import Doctor

class Role(str, PyEnum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="user_role_enum", create_type=True), 
        nullable=False, 
        default=Role.PATIENT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 2. Use string forward references. The IDE now knows what "Patient" and "Doctor" are.
    patient_profile: Mapped["Patient"] = relationship(back_populates="user", cascade="all, delete-orphan")
    doctor_profile: Mapped["Doctor"] = relationship(back_populates="user", cascade="all, delete-orphan")