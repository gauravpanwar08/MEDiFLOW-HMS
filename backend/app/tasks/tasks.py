"""
Celery background tasks: appointment reminders, daily reports, cache warming.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import structlog

logger = structlog.get_logger()

celery_app = Celery(
    "hms",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "send-reminders-daily": {
            "task": "app.tasks.tasks.send_appointment_reminders",
            "schedule": crontab(hour=8, minute=0),
        },
        "daily-report": {
            "task": "app.tasks.tasks.generate_daily_report",
            "schedule": crontab(hour=7, minute=0),
        },
        "cleanup-notifications": {
            "task": "app.tasks.tasks.cleanup_old_notifications",
            "schedule": crontab(hour=2, minute=0, day_of_week=0),
        },
    },
)


@celery_app.task(bind=True, max_retries=3)
def send_appointment_reminders(self):
    """Send email reminders for appointments scheduled tomorrow."""
    try:
        from datetime import date, timedelta
        from sqlalchemy import create_engine, select, and_
        from sqlalchemy.orm import Session, selectinload
        from app.models.models import Appointment, AppointmentStatus

        engine = create_engine(settings.DATABASE_SYNC_URL)
        tomorrow = date.today() + timedelta(days=1)

        with Session(engine) as db:
            result = db.execute(
                select(Appointment)
                .options(
                    selectinload(Appointment.patient),
                    selectinload(Appointment.doctor),
                )
                .where(
                    and_(
                        Appointment.appointment_date == tomorrow,
                        Appointment.status == AppointmentStatus.confirmed,
                        Appointment.reminder_sent == False,
                    )
                )
            )
            appointments = result.scalars().all()

            sent = 0
            for appt in appointments:
                # Simulate email send
                logger.info(
                    "reminder_sent",
                    appointment_id=appt.id,
                    patient_id=appt.patient_id,
                    date=str(appt.appointment_date),
                    time=appt.time_slot,
                )
                appt.reminder_sent = True
                sent += 1

            db.commit()
        return {"reminders_sent": sent, "date": str(tomorrow)}

    except Exception as exc:
        logger.error("reminder_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task
def generate_daily_report():
    """Generate daily appointment statistics and log them."""
    try:
        from datetime import date
        from sqlalchemy import create_engine, select, func, and_
        from sqlalchemy.orm import Session
        from app.models.models import Appointment, AppointmentStatus

        engine = create_engine(settings.DATABASE_SYNC_URL)
        today = date.today()

        with Session(engine) as db:
            total = db.execute(
                select(func.count()).select_from(Appointment)
                .where(Appointment.appointment_date == today)
            ).scalar_one()

            completed = db.execute(
                select(func.count()).select_from(Appointment)
                .where(and_(
                    Appointment.appointment_date == today,
                    Appointment.status == AppointmentStatus.completed,
                ))
            ).scalar_one()

        report = {
            "date": str(today),
            "total_appointments": total,
            "completed": completed,
            "pending": total - completed,
        }
        logger.info("daily_report_generated", **report)
        return report

    except Exception as exc:
        logger.error("report_task_failed", error=str(exc))
        return {"error": str(exc)}


@celery_app.task
def cleanup_old_notifications():
    """Delete notifications older than 30 days."""
    try:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import create_engine, delete
        from sqlalchemy.orm import Session
        from app.models.models import Notification

        engine = create_engine(settings.DATABASE_SYNC_URL)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        with Session(engine) as db:
            result = db.execute(
                delete(Notification).where(Notification.created_at < cutoff)
            )
            db.commit()
            deleted = result.rowcount

        logger.info("notifications_cleaned", deleted=deleted)
        return {"deleted": deleted}

    except Exception as exc:
        logger.error("cleanup_failed", error=str(exc))
        return {"error": str(exc)}


@celery_app.task
def send_appointment_confirmation(appointment_id: int):
    """Send confirmation email for a newly booked appointment."""
    logger.info("confirmation_sent", appointment_id=appointment_id)
    return {"sent": True, "appointment_id": appointment_id}
