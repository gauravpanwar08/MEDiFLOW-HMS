
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import timedelta

from app.db.session import get_db
from app.domains.users.models import User
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from pydantic import BaseModel
from app.core.logging import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {credentials.email}")
    
    user = db.execute(select(User).where(User.email == credentials.email)).scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {user.email}")
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

from app.core.security import get_password_hash

@router.post("/register")
def register(user_in: LoginRequest, db: Session = Depends(get_db)):
    existing_user = db.execute(
        select(User).where(User.email == user_in.email)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role="patient"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}