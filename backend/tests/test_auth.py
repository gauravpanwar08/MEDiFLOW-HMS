import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.db.session import Base, get_db
from app.models.models import Hospital, User, Patient
from app.core.security import verify_password, get_password_hash

from tests.conftest import TestSessionLocal, test_engine


@pytest.fixture(scope="function", autouse=True)
async def seed_hospital():
    # Seed default hospital
    async with TestSessionLocal() as session:
        h = Hospital(
            name="City General Hospital",
            slug="default",
            address="123 Medical Centre Road",
            phone="+91 22 1234 5678",
            email="admin@citygeneral.hospital",
            is_active=True,
            subscription_plan="enterprise",
        )
        session.add(h)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def register_patient(ac: AsyncClient, email: str = "aarav.patel@example.com", password: str = "Password123!"):
    payload = {
        "first_name": "Aarav",
        "last_name": "Patel",
        "email": email,
        "password": password,
        "phone": "+91 98765 43210",
        "hospital_slug": "default",
    }
    return await ac.post("/api/v1/auth/register", json=payload)


@pytest.mark.asyncio
async def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


@pytest.mark.asyncio
async def test_patient_registration_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await register_patient(ac, "aarav.patel@example.com", "Password123!")
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "aarav.patel@example.com"
        assert data["role"] == "patient"
        assert data["is_active"] is True
        assert data["first_name"] == "Aarav"

        # Verify Patient record was created in database
        async with TestSessionLocal() as db:
            result = await db.execute(select(Patient).where(Patient.user_id == data["id"]))
            patient = result.scalar_one_or_none()
            assert patient is not None
            assert patient.user_id == data["id"]


@pytest.mark.asyncio
async def test_public_registration_prevents_privilege_escalation():
    """Ensure submitting role: 'admin' or 'doctor' still produces a patient account."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "first_name": "Malicious",
            "last_name": "Actor",
            "email": "hacker@example.com",
            "password": "Password123!",
            "role": "admin",
            "hospital_slug": "default",
        }
        res = await ac.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["role"] == "patient", "Public registration must force role to patient"


@pytest.mark.asyncio
async def test_registration_duplicate_email_conflict():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res1 = await register_patient(ac, "duplicate@example.com", "Password123!")
        assert res1.status_code == 201

        # Attempt registering same email again
        res2 = await register_patient(ac, "duplicate@example.com", "Password123!")
        assert res2.status_code == 409
        assert "already registered" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_registration_case_insensitive_duplicate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res1 = await register_patient(ac, "mixed.case@example.com", "Password123!")
        assert res1.status_code == 201

        # Attempt registering same email with different case
        res2 = await register_patient(ac, "MIXED.CASE@EXAMPLE.COM", "Password123!")
        assert res2.status_code == 409


@pytest.mark.asyncio
async def test_registration_short_password_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "first_name": "Short",
            "last_name": "Pass",
            "email": "short@example.com",
            "password": "short",  # < 8 chars
            "hospital_slug": "default",
        }
        res = await ac.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success_and_get_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg_res = await register_patient(ac, "login.user@example.com", "Password123!")
        assert reg_res.status_code == 201

        login_res = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "login.user@example.com",
                "password": "Password123!",
                "hospital_slug": "default",
            },
        )
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["role"] == "patient"

        # Call protected /auth/me
        me_res = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me_res.status_code == 200
        user_info = me_res.json()
        assert user_info["email"] == "login.user@example.com"
        assert user_info["first_name"] == "Aarav"


@pytest.mark.asyncio
async def test_login_case_insensitive_email():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg_res = await register_patient(ac, "case.user@example.com", "Password123!")
        assert reg_res.status_code == 201

        login_res = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "CASE.USER@EXAMPLE.COM",  # Uppercase login attempt
                "password": "Password123!",
                "hospital_slug": "default",
            },
        )
        assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_login_invalid_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg_res = await register_patient(ac, "wrong.pass@example.com", "Password123!")
        assert reg_res.status_code == 201

        res = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong.pass@example.com",
                "password": "WrongPassword999!",
                "hospital_slug": "default",
            },
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "Password123!",
                "hospital_slug": "default",
            },
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg_res = await register_patient(ac, "refresh.user@example.com", "Password123!")
        assert reg_res.status_code == 201

        login_res = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh.user@example.com",
                "password": "Password123!",
                "hospital_slug": "default",
            },
        )
        refresh_token = login_res.json()["refresh_token"]

        ref_res = await ac.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert ref_res.status_code == 200
        new_tokens = ref_res.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens


@pytest.mark.asyncio
async def test_unauthorized_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/auth/me")
        assert res.status_code == 401
