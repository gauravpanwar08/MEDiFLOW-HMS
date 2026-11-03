import os
import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import Base, get_db
from app.models.models import Hospital, User, Patient, Doctor, DoctorSpecialty, Appointment, AppointmentStatus, AppointmentPriority
from app.core.security import get_password_hash, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_endpoints.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        h = Hospital(name="City Hospital", slug="default", is_active=True)
        db.add(h)
        await db.flush()

        admin_user = User(
            hospital_id=h.id,
            email="admin@hospital.com",
            hashed_password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
        )
        db.add(admin_user)

        doc_user = User(
            hospital_id=h.id,
            email="doctor@hospital.com",
            hashed_password=get_password_hash("doctor123"),
            first_name="Alice",
            last_name="Doctor",
            role="doctor",
            is_active=True,
        )
        db.add(doc_user)
        await db.flush()

        doc = Doctor(
            hospital_id=h.id,
            user_id=doc_user.id,
            specialty=DoctorSpecialty.general_physician,
            license_number="LIC-123",
            experience_years=5,
            consultation_fee=500.0,
            is_available=True,
        )
        db.add(doc)

        pat_user = User(
            hospital_id=h.id,
            email="patient@hospital.com",
            hashed_password=get_password_hash("patient123"),
            first_name="Bob",
            last_name="Patient",
            role="patient",
            is_active=True,
        )
        db.add(pat_user)
        await db.flush()

        pat = Patient(hospital_id=h.id, user_id=pat_user.id)
        db.add(pat)
        await db.flush()

        appt = Appointment(
            hospital_id=h.id,
            patient_id=pat.id,
            doctor_id=doc.id,
            appointment_date=date.today(),
            time_slot="10:00",
            duration_minutes=30,
            status=AppointmentStatus.confirmed,
            priority=AppointmentPriority.routine,
        )
        db.add(appt)
        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_endpoints.db"):
        os.remove("./test_endpoints.db")


@pytest.mark.asyncio
async def test_appointments_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token({"sub": "1", "role": "admin", "hospital_id": 1, "hospital_slug": "default"})
        res = await client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, res.text
        data = res.json()
        assert "items" in data
        assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_analytics_trends_and_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token({"sub": "1", "role": "admin", "hospital_id": 1, "hospital_slug": "default"})
        res1 = await client.get("/api/v1/analytics/trends?days=30", headers={"Authorization": f"Bearer {token}"})
        assert res1.status_code == 200, res1.text
        assert isinstance(res1.json(), list)

        res2 = await client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 200, res2.text
        assert res2.json()["total_appointments"] >= 1

        res3 = await client.get("/api/v1/analytics/doctor-workload", headers={"Authorization": f"Bearer {token}"})
        assert res3.status_code == 200, res3.text
        assert isinstance(res3.json(), list)


@pytest.mark.asyncio
async def test_records_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token({"sub": "1", "role": "admin", "hospital_id": 1, "hospital_slug": "default"})
        res = await client.get("/api/v1/records", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, res.text
        data = res.json()
        assert "items" in data


@pytest.mark.asyncio
async def test_book_appointment_for_patient():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token({"sub": "1", "role": "admin", "hospital_id": 1, "hospital_slug": "default"})
        payload = {
            "doctor_id": 1,
            "patient_id": 1,
            "appointment_date": "2026-12-15",
            "time_slot": "11:30",
            "reason": "Checkup",
            "priority": "routine"
        }
        res = await client.post("/api/v1/appointments", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["doctor_id"] == 1
        assert data["patient_id"] == 1
