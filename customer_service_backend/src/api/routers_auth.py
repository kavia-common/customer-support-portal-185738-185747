from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.core.security import get_password_hash, verify_password
from src.db.models import User
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email for login")
    full_name: Optional[str] = Field(None, description="Full name")
    password: str = Field(..., min_length=6, description="Password")
    is_agent: bool = Field(False, description="Set true to register as agent")


# PUBLIC_INTERFACE
@router.post(
    "/register",
    summary="Register user (no auth)",
    description="Register a new user account without issuing tokens.",
)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a user without returning a JWT."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        is_agent=payload.is_agent,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "registered", "user_id": user.id}


# PUBLIC_INTERFACE
@router.post(
    "/login",
    summary="User login (no-op)",
    description="No authentication is required; endpoint is a no-op for compatibility.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """No-op login for compatibility; always returns a placeholder token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # To avoid leaking existence, still return 401 here
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return {"access_token": "disabled-auth", "token_type": "none"}


# PUBLIC_INTERFACE
@router.get(
    "/me",
    summary="Current user (no-op)",
    description="Auth disabled; returns a placeholder profile.",
)
def me():
    """Return a placeholder indicating auth is disabled."""
    return {"message": "authentication disabled"}
