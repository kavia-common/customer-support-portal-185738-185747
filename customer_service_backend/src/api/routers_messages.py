from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.models import Message, Ticket, User
from src.db.schemas import MessageCreate, MessagePublic
from src.db.session import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=MessagePublic,
    summary="Post a message",
    description="Post a message to a ticket. Customers must own the ticket; agents can post to any.",
)
def post_message(payload: MessageCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a message in a ticket conversation with RBAC checks."""
    ticket = db.query(Ticket).filter(Ticket.id == payload.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not current.is_agent and ticket.creator_id != current.id:
        raise HTTPException(status_code=403, detail="Not authorized to post to this ticket")
    if payload.author_id != current.id:
        raise HTTPException(status_code=403, detail="Cannot post as another user")

    msg = Message(ticket_id=payload.ticket_id, author_id=payload.author_id, content=payload.content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# PUBLIC_INTERFACE
@router.get(
    "/ticket/{ticket_id}",
    response_model=List[MessagePublic],
    summary="List messages by ticket",
    description="List messages for a ticket. Customers must own the ticket; agents can view any.",
)
def list_messages(ticket_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List messages for a ticket with RBAC."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not current.is_agent and ticket.creator_id != current.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket's messages")
    return db.query(Message).filter(Message.ticket_id == ticket_id).order_by(Message.created_at.asc()).all()
