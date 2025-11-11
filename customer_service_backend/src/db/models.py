from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    ForeignKey,
    DateTime,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.session import Base


class User(Base):
    """User account model representing both customers and agents."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_agent: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tickets_created: Mapped[List["Ticket"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan", foreign_keys="Ticket.creator_id"
    )
    tickets_assigned: Mapped[List["Ticket"]] = relationship(
        back_populates="assignee", foreign_keys="Ticket.assignee_id"
    )
    messages: Mapped[List["Message"]] = relationship(back_populates="author")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"User(id={self.id!r}, email={self.email!r})"


class Ticket(Base):
    """Support ticket opened by a user and optionally assigned to an agent."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)

    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    creator: Mapped["User"] = relationship(back_populates="tickets_created", foreign_keys=[creator_id])
    assignee: Mapped[Optional["User"]] = relationship(back_populates="tickets_assigned", foreign_keys=[assignee_id])
    messages: Mapped[List["Message"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    __table_args__ = (
        Index("ix_tickets_status", "status"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Ticket(id={self.id!r}, title={self.title!r}, status={self.status!r})"


class Message(Base):
    """Message in a ticket conversation posted by a user or an agent."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="messages")
    author: Mapped["User"] = relationship(back_populates="messages")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Message(id={self.id!r}, ticket_id={self.ticket_id!r})"
