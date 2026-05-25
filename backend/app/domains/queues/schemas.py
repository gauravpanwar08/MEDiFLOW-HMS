import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.domains.queues.models import QueueStatus

class QueueJoin(BaseModel):
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID

class QueueStatusUpdate(BaseModel):
    status: QueueStatus

class QueueResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID
    position: int
    status: QueueStatus
    estimated_time_mins: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)