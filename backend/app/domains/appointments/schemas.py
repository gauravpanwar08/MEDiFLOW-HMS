import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.domains.appointments.models import AppointmentStatus, AppointmentPriority

class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_time: datetime
    priority: AppointmentPriority = AppointmentPriority.NORMAL

class AppointmentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_time: datetime
    status: AppointmentStatus
    priority: AppointmentPriority
    created_at: datetime

    # ConfigDict allows Pydantic to read data directly from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)