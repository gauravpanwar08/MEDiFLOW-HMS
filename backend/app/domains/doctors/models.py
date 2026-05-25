import uuid
from sqlalchemy import String, Integer, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.appointments.models import Appointment
from app.domains.users.models import User
from app.db.base import Base
from app.db.mixins import TimestampMixin

class Doctor(Base, TimestampMixin):
    """
    Domain model for Doctor-specific data.
    """
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    
    # unique=True guarantees a strict 1-to-1 relationship with User
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    
    specialization: Mapped[str] = mapped_column(String(100), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)

    # Link back to the User model
    user: Mapped["User"] = relationship(back_populates="doctor_profile")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="doctor")
    