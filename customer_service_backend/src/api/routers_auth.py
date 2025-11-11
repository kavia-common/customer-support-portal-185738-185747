from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.core.security import create_access_token, get_password_hash, verify_password, get_current_user
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
    response_model=TokenResponse,
    summary="Register user",
    description="Register a new user account and return a JWT access token.",
)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register user and return token."""
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

    token = create_access_token(
        {"sub": user.email, "is_agent": user.is_agent, "user_id": user.id}
    )
    return TokenResponse(access_token=token, token_type="bearer")


# PUBLIC_INTERFACE
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password to obtain JWT access token.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with OAuth2 form (username=email)."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token({"sub": user.email, "is_agent": user.is_agent, "user_id": user.id})
    return TokenResponse(access_token=token, token_type="bearer")


# PUBLIC_INTERFACE
@router.get(
    "/me",
    summary="Current user",
    description="Retrieve the current authenticated user's profile.",
)
def me(user: User = Depends(get_current_user)):
    """Return minimal current user info."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_agent": user.is_agent,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }
