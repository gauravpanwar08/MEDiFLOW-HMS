from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.models import Hospital, User, AuditAction
from app.schemas.schemas import UserCreate, UserOut, UserUpdate, Token, TokenRefresh, LoginRequest
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_hospital(db: AsyncSession, slug: str) -> Hospital:
    result = await db.execute(
        select(Hospital).where(and_(Hospital.slug == slug, Hospital.is_active == True))
    )
    h = result.scalar_one_or_none()
    if not h:
        raise HTTPException(404, f"Hospital '{slug}' not found")
    return h


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    hospital = await get_hospital(db, data.hospital_slug)
    if await UserService.get_by_email(db, data.email, hospital.id):
        raise HTTPException(409, "Email already registered")
    user = await UserService.create(db, data, hospital)
    await AuditService.log(
        db, AuditAction.create, "user", user.id, hospital_id=hospital.id,
        new_values={"email": user.email, "role": user.role.value},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    hospital = await get_hospital(db, data.hospital_slug)
    user = await UserService.get_by_email(db, data.email, hospital.id)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(403, "Account deactivated")
    payload = {
        "sub": str(user.id), "role": user.role.value,
        "hospital_id": hospital.id, "hospital_slug": hospital.slug,
    }
    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    await AuditService.log(
        db, AuditAction.login, "user", user.id,
        user_id=user.id, hospital_id=hospital.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return Token(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        user_id=user.id, role=user.role.value,
    )


@router.post("/refresh", response_model=Token)
async def refresh(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user = await UserService.get_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    p = {
        "sub": str(user.id), "role": user.role.value,
        "hospital_id": payload["hospital_id"], "hospital_slug": payload.get("hospital_slug", ""),
    }
    return Token(
        access_token=create_access_token(p), refresh_token=create_refresh_token(p),
        user_id=user.id, role=user.role.value,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, val)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AuditService.log(
        db, AuditAction.logout, "user", current_user.id,
        user_id=current_user.id, hospital_id=current_user.hospital_id,
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Logged out"}
