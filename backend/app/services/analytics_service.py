from datetime import date, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.models import Appointment, Doctor, Patient, User, AppointmentStatus
from app.schemas.schemas import AnalyticsSummary, DoctorWorkload
from app.db.cache import cache


class AnalyticsService:

    @staticmethod
    async def get_summary(db: AsyncSession, hospital_id: int) -> AnalyticsSummary:
        cache_key = f"analytics:summary:{hospital_id}"
        cached = await cache.get(cache_key)
        if cached:
            return AnalyticsSummary(**cached)

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        async def count_appts(*conditions):
            q = select(func.count()).select_from(Appointment).where(
                Appointment.hospital_id == hospital_id, *conditions)
            return (await db.execute(q)).scalar_one()

        total_patients = (await db.execute(
            select(func.count()).select_from(Patient).where(Patient.hospital_id == hospital_id)
        )).scalar_one()
        total_doctors = (await db.execute(
            select(func.count()).select_from(Doctor).where(Doctor.hospital_id == hospital_id)
        )).scalar_one()
        total_appts = await count_appts()
        today_appts = await count_appts(Appointment.appointment_date == today)
        week_appts = await count_appts(Appointment.appointment_date >= week_start)
        month_appts = await count_appts(Appointment.appointment_date >= month_start)
        pending = await count_appts(Appointment.status == AppointmentStatus.pending)
        completed = await count_appts(Appointment.status == AppointmentStatus.completed)
        cancelled = await count_appts(Appointment.status == AppointmentStatus.cancelled)

        revenue_q = (
            select(func.coalesce(func.sum(Doctor.consultation_fee), 0))
            .join(Appointment, Appointment.doctor_id == Doctor.id)
            .where(and_(
                Appointment.hospital_id == hospital_id,
                Appointment.status == AppointmentStatus.completed,
                Appointment.appointment_date >= month_start,
            ))
        )
        revenue = float((await db.execute(revenue_q)).scalar_one())

        summary = AnalyticsSummary(
            total_patients=total_patients,
            total_doctors=total_doctors,
            total_appointments=total_appts,
            appointments_today=today_appts,
            appointments_this_week=week_appts,
            appointments_this_month=month_appts,
            pending_appointments=pending,
            completed_appointments=completed,
            cancelled_appointments=cancelled,
            revenue_this_month=revenue,
        )
        await cache.set(cache_key, summary.model_dump(), ttl=300)
        return summary

    @staticmethod
    async def get_doctor_workloads(db: AsyncSession, hospital_id: int) -> List[DoctorWorkload]:
        cache_key = f"analytics:workload:{hospital_id}"
        cached = await cache.get(cache_key)
        if cached:
            return [DoctorWorkload(**d) for d in cached]

        month_start = date.today().replace(day=1)
        result = await db.execute(
            select(
                Doctor.id,
                User.first_name,
                User.last_name,
                Doctor.specialty,
                Doctor.rating,
                func.count(Appointment.id).label("total"),
                func.sum(func.cast(Appointment.status == AppointmentStatus.completed, Integer=True)).label("completed"),
                func.sum(func.cast(Appointment.status == AppointmentStatus.pending, Integer=True)).label("pending"),
                func.sum(func.cast(Appointment.status == AppointmentStatus.cancelled, Integer=True)).label("cancelled"),
            )
            .join(User, Doctor.user_id == User.id)
            .outerjoin(Appointment, and_(
                Appointment.doctor_id == Doctor.id,
                Appointment.appointment_date >= month_start,
            ))
            .where(Doctor.hospital_id == hospital_id)
            .group_by(Doctor.id, User.first_name, User.last_name, Doctor.specialty, Doctor.rating)
        )
        rows = result.fetchall()
        workloads = [
            DoctorWorkload(
                doctor_id=row[0],
                doctor_name=f"Dr. {row[1]} {row[2]}",
                specialty=row[3].value if row[3] else "",
                avg_rating=float(row[4] or 0),
                total_appointments=int(row[5] or 0),
                completed=int(row[6] or 0),
                pending=int(row[7] or 0),
                cancelled=int(row[8] or 0),
            )
            for row in rows
        ]
        await cache.set(cache_key, [w.model_dump() for w in workloads], ttl=300)
        return workloads

    @staticmethod
    async def get_trends(db: AsyncSession, hospital_id: int, days: int = 30) -> List[dict]:
        cache_key = f"analytics:trends:{hospital_id}:{days}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        start = date.today() - timedelta(days=days)
        result = await db.execute(
            select(Appointment.appointment_date, func.count(Appointment.id).label("count"))
            .where(and_(
                Appointment.hospital_id == hospital_id,
                Appointment.appointment_date >= start,
            ))
            .group_by(Appointment.appointment_date)
            .order_by(Appointment.appointment_date)
        )
        trends = [{"date": str(row[0]), "count": row[1]} for row in result.fetchall()]
        await cache.set(cache_key, trends, ttl=600)
        return trends
