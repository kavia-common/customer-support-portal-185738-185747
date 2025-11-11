from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.db.models import User
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email for identification")
    full_name: Optional[str] = Field(None, description="Full name")
    # Keep is_agent flag to allow agent UI in frontend if desired
    is_agent: bool = Field(False, description="Set true to register as agent")


# PUBLIC_INTERFACE
@router.post(
    "/register",
    summary="Register user (no auth, no password)",
    description="Register a new user account without passwords or tokens.",
)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a user without password requirements and return a lightweight session object."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        # Registration is idempotent: return existing "session" for same email
        return {"message": "already_registered", "user_id": existing.id, "access_token": "auth-disabled", "token_type": "none"}

    # Store a dummy password to satisfy non-null DB constraint
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password="!",  # placeholder to satisfy NOT NULL; auth disabled
        is_agent=payload.is_agent,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Return a simple token placeholder for frontend compatibility
    return {"message": "registered", "user_id": user.id, "access_token": "auth-disabled", "token_type": "none"}


# PUBLIC_INTERFACE
@router.post(
    "/login",
    summary="Login (no-op, no password)",
    description="Always succeeds and returns a placeholder token; no password required.",
)
def login(username: str, db: Session = Depends(get_db)):
    """No-op login for compatibility; ensure a user exists by email and return a placeholder token."""
    user = db.query(User).filter(User.email == username).first()
    if not user:
        # Auto-create user if not present
        user = User(email=username, full_name=None, hashed_password="!", is_agent=False, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"access_token": "auth-disabled", "token_type": "none", "user_id": user.id}


# PUBLIC_INTERFACE
@router.get(
    "/me",
    summary="Current user (no-auth public)",
    description="Returns a placeholder profile without requiring Authorization headers.",
)
def me():
    """Return a trivial profile indicating auth is disabled and anonymous access is allowed."""
    return {"id": None, "email": None, "is_agent": False, "note": "authentication disabled; anonymous access"}
