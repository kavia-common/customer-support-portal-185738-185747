from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.security import get_current_user, require_agent, get_password_hash
from src.db.models import User
from src.db.schemas import UserPublic
from src.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name")
    password: Optional[str] = Field(None, min_length=6, description="New password")


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=List[UserPublic],
    summary="List users (agent only)",
    description="List all users. Requires agent role.",
)
def list_users(_: User = Depends(require_agent), db: Session = Depends(get_db)):
    """List all users for admin/agent."""
    return db.query(User).all()


# PUBLIC_INTERFACE
@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Get user by ID",
    description="Get a user by ID. Agents can view any user; others only themselves.",
)
def get_user_by_id(user_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user details with RBAC."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current.is_agent and current.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    return user


# PUBLIC_INTERFACE
@router.put(
    "/{user_id}",
    response_model=UserPublic,
    summary="Update user",
    description="Update user details. Agents can update any user; others only themselves.",
)
def update_user(user_id: int, payload: UserUpdateRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile/password with RBAC."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current.is_agent and current.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password:
        user.hashed_password = get_password_hash(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
