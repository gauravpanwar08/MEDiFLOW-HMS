from typing import Optional, List, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from app.models.models import (
    Appointment, Doctor, Patient, DoctorAvailability,
    AppointmentStatus, AppointmentPriority, Notification
)
from app.schemas.schemas import AppointmentCreate, AppointmentUpdate, AvailableSlot
from app.db.cache import cache


class AppointmentService:

    @staticmethod
    async def get_available_slots(db: AsyncSession, doctor_id: int, for_date: date) -> List[AvailableSlot]:
        cache_key = f"slots:{doctor_id}:{for_date}"
        cached = await cache.get(cache_key)
        if cached:
            return [AvailableSlot(**s) for s in cached]

        day_of_week = for_date.weekday()
        avail_result = await db.execute(
            select(DoctorAvailability).where(and_(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.day_of_week == day_of_week,
                DoctorAvailability.is_active == True,
            ))
        )
        availability = avail_result.scalars().all()

        booked_result = await db.execute(
            select(Appointment.time_slot).where(and_(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == for_date,
                Appointment.status.notin_([AppointmentStatus.cancelled]),
            ))
        )
        booked = {r[0] for r in booked_result.fetchall()}

        slots = []
        for avail in availability:
            start = datetime.strptime(avail.start_time, "%H:%M")
            end = datetime.strptime(avail.end_time, "%H:%M")
            current = start
            while current < end:
                s = current.strftime("%H:%M")
                slots.append(AvailableSlot(time=s, available=s not in booked))
                current += timedelta(minutes=avail.slot_duration_minutes)

        await cache.set(cache_key, [s.model_dump() for s in slots], ttl=60)
        return slots

    @staticmethod
    async def check_slot_free(db: AsyncSession, doctor_id: int, appt_date: date, time_slot: str) -> bool:
        result = await db.execute(
            select(Appointment).where(and_(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appt_date,
                Appointment.time_slot == time_slot,
                Appointment.status.notin_([AppointmentStatus.cancelled]),
            ))
        )
        return result.scalar_one_or_none() is None

    @staticmethod
    async def create(db: AsyncSession, hospital_id: int, patient_id: int,
                     data: AppointmentCreate) -> Appointment:
        doctor = await db.get(Doctor, data.doctor_id)
        if not doctor or doctor.hospital_id != hospital_id:
            raise ValueError("Doctor not found in this hospital")
        if not doctor.is_available:
            raise ValueError("Doctor is currently unavailable")

        if data.priority != AppointmentPriority.emergency:
            if not await AppointmentService.check_slot_free(db, data.doctor_id, data.appointment_date, data.time_slot):
                raise ValueError(f"Slot {data.time_slot} on {data.appointment_date} is already booked")

        appt = Appointment(
            hospital_id=hospital_id,
            patient_id=patient_id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            time_slot=data.time_slot,
            reason=data.reason,
            symptoms=data.symptoms,
            priority=data.priority,
            status=AppointmentStatus.confirmed if data.priority == AppointmentPriority.emergency else AppointmentStatus.pending,
        )
        db.add(appt)
        await db.flush()
        await db.refresh(appt)

        await cache.delete(f"slots:{data.doctor_id}:{data.appointment_date}")
        await cache.publish("appointment_events", {
            "event": "appointment_created",
            "appointment_id": appt.id,
            "hospital_id": hospital_id,
            "doctor_id": data.doctor_id,
            "priority": data.priority.value,
        })

        notif = Notification(
            hospital_id=hospital_id,
            user_id=doctor.user_id,
            title="New Appointment",
            message=f"{'🚨 EMERGENCY: ' if data.priority == AppointmentPriority.emergency else ''}New appointment on {data.appointment_date} at {data.time_slot}",
            notification_type="alert" if data.priority == AppointmentPriority.emergency else "info",
            meta={"appointment_id": appt.id},
        )
        db.add(notif)
        return appt

    @staticmethod
    async def update(db: AsyncSession, appt: Appointment, data: AppointmentUpdate) -> Appointment:
        old_status = appt.status
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(appt, field, value)
        await db.flush()
        await db.refresh(appt)
        if appt.status != old_status:
            await cache.delete(f"slots:{appt.doctor_id}:{appt.appointment_date}")
            await cache.publish("appointment_events", {
                "event": "status_changed",
                "appointment_id": appt.id,
                "new_status": appt.status.value,
            })
        return appt

    @staticmethod
    async def list_appointments(
        db: AsyncSession, hospital_id: int,
        page: int = 1, page_size: int = 20,
        search: Optional[str] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[AppointmentStatus] = None,
        priority: Optional[AppointmentPriority] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[Appointment], int]:
        query = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.doctor).selectinload(Doctor.user),
            )
            .where(Appointment.hospital_id == hospital_id)
        )
        if doctor_id:
            query = query.where(Appointment.doctor_id == doctor_id)
        if patient_id:
            query = query.where(Appointment.patient_id == patient_id)
        if status:
            query = query.where(Appointment.status == status)
        if priority:
            query = query.where(Appointment.priority == priority)
        if date_from:
            query = query.where(Appointment.appointment_date >= date_from)
        if date_to:
            query = query.where(Appointment.appointment_date <= date_to)
        if search:
            s = f"%{search}%"
            query = query.where(or_(Appointment.reason.ilike(s), Appointment.symptoms.ilike(s)))

        priority_order = case(
            {AppointmentPriority.emergency.value: 0,
             AppointmentPriority.urgent.value: 1,
             AppointmentPriority.routine.value: 2},
            value=Appointment.priority,
        )
        query = query.order_by(priority_order, Appointment.appointment_date, Appointment.time_slot)

        total = (await db.execute(
            select(func.count()).select_from(
                select(Appointment).where(Appointment.hospital_id == hospital_id).subquery()
            )
        )).scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_by_id(db: AsyncSession, appt_id: int, hospital_id: int) -> Optional[Appointment]:
        result = await db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.doctor).selectinload(Doctor.user),
            )
            .where(and_(Appointment.id == appt_id, Appointment.hospital_id == hospital_id))
        )
        return result.scalar_one_or_none()
