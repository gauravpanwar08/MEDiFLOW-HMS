from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.domains.queues.models import Queue, QueueStatus
from app.domains.queues.schemas import QueueJoin, QueueStatusUpdate, QueueResponse
from app.infrastructure.websocket_manager import manager
from app.domains.queues.services import recalculate_doctor_queue

router = APIRouter(prefix="/queues", tags=["Queues"])

def get_queue_data(db: Session, doctor_id: uuid.UUID) -> list[dict]:
    """Helper to fetch and serialize the current active queue for a doctor."""
    queue_entries = db.execute(
        select(Queue)
        .where(Queue.doctor_id == doctor_id, Queue.status != QueueStatus.DONE)
        .order_by(Queue.position.asc())
    ).scalars().all()
    # Serialize to JSON-compatible dictionaries for WebSockets
    return [QueueResponse.model_validate(q).model_dump(mode="json") for q in queue_entries]

@router.websocket("/ws/{doctor_id}")
async def websocket_queue_endpoint(websocket: WebSocket, doctor_id: uuid.UUID, db: Session = Depends(get_db)):
    """WebSocket endpoint. Clients connect here to listen to live queue updates."""
    await manager.connect(websocket, doctor_id)
    try:
        # Send initial state immediately upon connection
        initial_queue = get_queue_data(db, doctor_id)
        await manager.broadcast_to_doctor_queue(doctor_id, initial_queue)

        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, doctor_id)

@router.post("/join", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def join_queue(queue_in: QueueJoin, db: Session = Depends(get_db)):
    # 1. Determine position
    max_pos_query = select(func.max(Queue.position)).where(
        Queue.doctor_id == queue_in.doctor_id,
        Queue.status != QueueStatus.DONE
    )
    max_position = db.execute(max_pos_query).scalar() or 0
    new_position = max_position + 1

    # Insert with ETA 0. The service layer will calculate the actual ETA.
    new_entry = Queue(
        doctor_id=queue_in.doctor_id,
        appointment_id=queue_in.appointment_id,
        position=new_position,
        estimated_time_mins=0
    )

    db.add(new_entry)
    try:
        db.commit()
        
        # 2. TRIGGER SERVICE: Recalculate times for everyone (including this new entry)
        recalculate_doctor_queue(db, queue_in.doctor_id)
        
        # 3. Refresh the entry so the HTTP API returns the accurately calculated ETA
        db.refresh(new_entry)
        
        # 4. BROADCAST: Push the newly updated queue to all connected screens
        updated_queue = get_queue_data(db, queue_in.doctor_id)
        await manager.broadcast_to_doctor_queue(queue_in.doctor_id, updated_queue)
        
        return new_entry
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment is already in the queue."
        )

@router.get("/{doctor_id}", response_model=List[QueueResponse])
def get_doctor_queue(doctor_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetch the active queue for a specific doctor."""
    queue_entries = db.execute(
        select(Queue)
        .where(Queue.doctor_id == doctor_id, Queue.status != QueueStatus.DONE)
        .order_by(Queue.position.asc())
    ).scalars().all()
    
    return queue_entries

@router.put("/{queue_id}/status", response_model=QueueResponse)
async def update_queue_status(queue_id: uuid.UUID, status_update: QueueStatusUpdate, db: Session = Depends(get_db)):
    """Used by the doctor to move a patient to IN_PROGRESS or DONE."""
    queue_entry = db.execute(select(Queue).where(Queue.id == queue_id)).scalar_one_or_none()
    
    if not queue_entry:
        raise HTTPException(status_code=404, detail="Queue entry not found")

    # Update status and commit
    queue_entry.status = status_update.status
    db.commit()
    
    # 1. TRIGGER SERVICE: A status change alters the ETA for everyone behind this patient
    recalculate_doctor_queue(db, queue_entry.doctor_id)
    
    # 2. Refresh current entry
    db.refresh(queue_entry)
    
    # 3. BROADCAST: Push the "Ripple Effect" ETA changes to all connected screens
    updated_queue = get_queue_data(db, queue_entry.doctor_id)
    await manager.broadcast_to_doctor_queue(queue_entry.doctor_id, updated_queue)
    
    return queue_entry