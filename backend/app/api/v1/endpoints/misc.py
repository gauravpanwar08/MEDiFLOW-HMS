"""
misc.py — Analytics, AI, Notifications, Audit Logs, Hospitals, WebSocket
"""
import json
import asyncio
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.models import User, Notification, Hospital, AuditLog, AuditAction
from app.schemas.schemas import (
    AnalyticsSummary, DoctorWorkload, NotificationOut, AuditLogOut,
    SymptomAnalysisRequest, SymptomAnalysisResponse, ChatMessage, ChatResponse,
    HospitalCreate, HospitalOut,
)
from app.core.security import get_current_user, require_admin
from app.core.config import settings
from app.services.analytics_service import AnalyticsService
from app.services.ai_service import AIService
from app.services.audit_service import AuditService
from app.db.cache import get_redis

# ── Analytics ────────────────────────────────────────────────────────────────
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_summary(db, current_user.hospital_id)


@analytics_router.get("/doctor-workload", response_model=List[DoctorWorkload])
async def doctor_workload(
    month: Optional[date] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_doctor_workloads(db, current_user.hospital_id, month)


@analytics_router.get("/trends")
async def appointment_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_appointment_trends(db, current_user.hospital_id, days)


# ── AI ───────────────────────────────────────────────────────────────────────
ai_router = APIRouter(prefix="/ai", tags=["AI"])


@ai_router.post("/symptom-analysis", response_model=SymptomAnalysisResponse)
async def symptom_analysis(
    data: SymptomAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    return await AIService.analyze_symptoms(data)


@ai_router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatMessage,
    current_user: User = Depends(get_current_user),
):
    return await AIService.chat(data.message, data.conversation_id)


# ── Notifications ─────────────────────────────────────────────────────────────
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("", response_model=List[NotificationOut])
async def list_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).limit(50)
    result = await db.execute(query)
    return result.scalars().all()


@notifications_router.post("/{notif_id}/read")
async def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notif_id, Notification.user_id == current_user.id)
        )
    )
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    await db.flush()
    return {"message": "Marked as read"}


@notifications_router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            and_(Notification.user_id == current_user.id, Notification.is_read == False)
        )
    )
    for n in result.scalars().all():
        n.is_read = True
    await db.flush()
    return {"message": "All marked as read"}


# ── Audit Logs ────────────────────────────────────────────────────────────────
audit_router = APIRouter(prefix="/audit", tags=["Audit"])


@audit_router.get("", tags=["Audit"])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    resource_type: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.schemas.schemas import PaginatedResponse, AuditLogOut
    from sqlalchemy.orm import selectinload
    query = (
        select(AuditLog).options(selectinload(AuditLog.user))
        .where(AuditLog.hospital_id == current_user.hospital_id)
        .order_by(AuditLog.created_at.desc())
    )
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    from sqlalchemy import func
    total = (await db.execute(select(func.count()).select_from(
        select(AuditLog).where(AuditLog.hospital_id == current_user.hospital_id).subquery()
    ))).scalar_one()
    query = query.offset((page - 1) * page_size).limit(page_size)
    logs = (await db.execute(query)).scalars().all()
    return PaginatedResponse(
        items=[AuditLogOut.model_validate(l).model_dump() for l in logs],
        total=total, page=page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


# ── Hospitals ─────────────────────────────────────────────────────────────────
hospitals_router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@hospitals_router.get("", response_model=List[HospitalOut])
async def list_hospitals(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).where(Hospital.is_active == True))
    return result.scalars().all()


@hospitals_router.post("", response_model=HospitalOut, status_code=201)
async def create_hospital(
    data: HospitalCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Hospital).where(Hospital.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Hospital slug already exists")
    h = Hospital(**data.model_dump())
    db.add(h)
    await db.flush()
    await db.refresh(h)
    return h


@hospitals_router.patch("/{hospital_id}", response_model=HospitalOut)
async def update_hospital(
    hospital_id: int,
    data: HospitalCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    h = await db.get(Hospital, hospital_id)
    if not h:
        raise HTTPException(404, "Hospital not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    await db.flush()
    await db.refresh(h)
    return h


# ── WebSocket ─────────────────────────────────────────────────────────────────
ws_router = APIRouter(tags=["WebSocket"])

active_connections: dict[int, list[WebSocket]] = {}


@ws_router.websocket("/ws/notifications/{user_id}")
async def ws_notifications(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)
    try:
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe("appointment_events")
        async def reader():
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                        await websocket.send_json(data)
                    except Exception:
                        pass
        task = asyncio.create_task(reader())
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if user_id in active_connections:
            active_connections[user_id] = [
                ws for ws in active_connections[user_id] if ws != websocket
            ]
        try:
            task.cancel()
        except Exception:
            pass
