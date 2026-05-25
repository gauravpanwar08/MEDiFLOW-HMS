import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domains.patients.models import Patient
    from app.domains.doctors.models import Doctor


# 🔹 Enums
class AppointmentStatus(str, PyEnum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AppointmentPriority(str, PyEnum):
    NORMAL = "NORMAL"
    EMERGENCY = "EMERGENCY"


# 🔹 Model
class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    # 🔥 Prevent double booking
    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "appointment_time",
            name="uq_doctor_appointment_time"
        ),
    )

    # 🔹 Primary Key (UUID)
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 🔹 Foreign Keys
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # 🔹 Appointment Time
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False
    )

    # 🔹 Status
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(
            AppointmentStatus,
            name="appointment_status_enum",
            create_type=True
        ),
        default=AppointmentStatus.SCHEDULED,
        nullable=False
    )

    # 🔹 Priority
    priority: Mapped[AppointmentPriority] = mapped_column(
        SQLEnum(
            AppointmentPriority,
            name="appointment_priority_enum",
            create_type=True
        ),
        default=AppointmentPriority.NORMAL,
        nullable=False
    )

    # 🔹 Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="appointments"
    )

    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="appointments"
    )