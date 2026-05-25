import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.domains.queues.models import Queue, QueueStatus

AVG_CONSULTATION_TIME_MINS = 10 


def recalculate_doctor_queue(
    db: Session,
    doctor_id: uuid.UUID
):
    active_entries = db.execute(
        select(Queue)
        .where(
            Queue.doctor_id == doctor_id,
            Queue.status != QueueStatus.DONE
        )
        .order_by(Queue.position.asc())
    ).scalars().all()

    if not active_entries:
        return

    patients_ahead = 0

    for entry in active_entries:
        if entry.status == QueueStatus.IN_PROGRESS:
            entry.estimated_time_mins = 0
            patients_ahead += 1

        elif entry.status == QueueStatus.WAITING:
            entry.estimated_time_mins = (
                patients_ahead * AVG_CONSULTATION_TIME_MINS
            )
            patients_ahead += 1

    db.commit()