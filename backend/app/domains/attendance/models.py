import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domains.patients.models import Patient
    from app.domains.appointments.models import Appointment

class Attendance(Base, TimestampMixin):
    """
    Historical ledger to track patient attendance for prediction logic.
    """
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Unique constraint ensures we don't record attendance twice for the same appointment
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    
    was_present: Mapped[bool] = mapped_column(Boolean, nullable=False)

    patient: Mapped["Patient"] = relationship(back_populates="attendance_records")
    appointment: Mapped["Appointment"] = relationship()
    