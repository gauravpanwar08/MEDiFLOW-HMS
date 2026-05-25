import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Boolean, Uuid, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domains.doctors.models import Doctor
    from app.domains.appointments.models import Appointment

class QueueStatus(str, PyEnum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class Queue(Base, TimestampMixin):
    __tablename__ = "queues"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Unique guarantees one queue entry per appointment
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    
    # Position in the line (1, 2, 3...)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    
    status: Mapped[QueueStatus] = mapped_column(
        SQLEnum(QueueStatus, name="queue_status_enum", create_type=True), 
        default=QueueStatus.WAITING, 
        nullable=False
    )
    
    # Simple integer for minutes. (e.g. 30 means 30 mins wait)
    estimated_time_mins: Mapped[int] = mapped_column(Integer, default=0)
    
    #FLAG: Tracks if the system automatically shifted this patient
    auto_reassigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships (unidirectional for now to keep things clean)
    doctor: Mapped["Doctor"] = relationship()
    appointment: Mapped["Appointment"] = relationship()