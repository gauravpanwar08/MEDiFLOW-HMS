import uuid
from sqlalchemy import String, Integer, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from typing import TYPE_CHECKING
from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domains.appointments.models import Appointment
    from app.domains.attendance.models import Attendance
    from app.domains.users.models import User

class Patient(Base, TimestampMixin):
    """
    Domain model for Patient-specific data.
    """
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    
    # unique=True guarantees a strict 1-to-1 relationship with User
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Link back to the User model (resolves via Base metadata registry)
    user: Mapped["User"] = relationship(back_populates="patient_profile")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="patient")
    
    attendance_records: Mapped[list["Attendance"]] = relationship(
    back_populates="patient",
    cascade="all, delete-orphan"
)
    