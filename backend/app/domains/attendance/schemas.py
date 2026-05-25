import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AttendanceCreate(BaseModel):
    patient_id: uuid.UUID
    appointment_id: uuid.UUID
    was_present: bool

class AttendanceResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    appointment_id: uuid.UUID
    was_present: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RiskProfileResponse(BaseModel):
    patient_id: uuid.UUID
    total_records: int
    missed_appointments: int
    risk_percentage: float
    risk_level: str