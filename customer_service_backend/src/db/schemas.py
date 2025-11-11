from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Unique email address for the user")
    full_name: Optional[str] = Field(None, description="Full name of the user")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Plaintext password to be hashed")


class UserPublic(UserBase):
    id: int = Field(..., description="User identifier")
    is_active: bool = Field(..., description="Whether the user is active")
    is_agent: bool = Field(..., description="If true, the user is a support agent")
    created_at: datetime = Field(..., description="Timestamp when the user was created")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated")

    class Config:
        from_attributes = True


# Ticket Schemas
class TicketBase(BaseModel):
    title: str = Field(..., description="Short title describing the issue")
    description: Optional[str] = Field(None, description="Detailed description of the issue")


class TicketCreate(TicketBase):
    creator_id: int = Field(..., description="ID of the user who created the ticket")
    assignee_id: Optional[int] = Field(None, description="ID of the agent assigned to the ticket, if any")


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    status: Optional[str] = Field(None, description="Updated status e.g., open, pending, closed")
    assignee_id: Optional[int] = Field(None, description="Assign/unassign agent")


class TicketPublic(TicketBase):
    id: int = Field(..., description="Ticket identifier")
    status: str = Field(..., description="Current status of the ticket")
    creator_id: int = Field(..., description="Creator user ID")
    assignee_id: Optional[int] = Field(None, description="Assigned agent user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    content: str = Field(..., description="Message text content")


class MessageCreate(MessageBase):
    ticket_id: int = Field(..., description="Ticket ID this message belongs to")
    author_id: int = Field(..., description="User ID of the message author")


class MessagePublic(MessageBase):
    id: int = Field(..., description="Message identifier")
    ticket_id: int = Field(..., description="Related ticket ID")
    author_id: int = Field(..., description="Author user ID")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
