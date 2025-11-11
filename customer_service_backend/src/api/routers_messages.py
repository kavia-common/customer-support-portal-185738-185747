from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.models import Message, Ticket
from src.db.schemas import MessageCreate, MessagePublic
from src.db.session import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=MessagePublic,
    summary="Post a message",
    description="Post a message to a ticket anonymously or with optional attribution by author_id.",
)
def post_message(payload: MessageCreate, db: Session = Depends(get_db)):
    """Create a message in a ticket conversation without authentication."""
    ticket = db.query(Ticket).filter(Ticket.id == payload.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

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
    description="List messages for a ticket without authentication.",
)
def list_messages(ticket_id: int, db: Session = Depends(get_db)):
    """List messages for a ticket without authentication."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db.query(Message).filter(Message.ticket_id == ticket_id).order_by(Message.created_at.asc()).all()
