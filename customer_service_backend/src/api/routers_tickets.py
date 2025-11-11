from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.db.models import Ticket
from src.db.schemas import TicketCreate, TicketPublic, TicketUpdate
from src.db.session import get_db

router = APIRouter(prefix="/tickets", tags=["tickets"])


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=TicketPublic,
    summary="Create ticket",
    description="Create a support ticket anonymously or with an optional creator_id if present.",
)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """Create a new support ticket without authentication.

    Authorization:
        None. Anyone can create a ticket.

    Behavior:
        - If payload.creator_id is provided, it will be stored; otherwise, the ticket is created
          without an associated creator (anonymous) when the schema/model allows it.
    """
    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        creator_id=payload.creator_id,
        assignee_id=payload.assignee_id,
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=List[TicketPublic],
    summary="List tickets",
    description="List tickets publicly; optionally filter by status.",
)
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List tickets without authentication with optional status filter."""
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    return q.order_by(Ticket.created_at.desc()).all()


# PUBLIC_INTERFACE
@router.get(
    "/{ticket_id}",
    response_model=TicketPublic,
    summary="Get ticket by ID",
    description="Retrieve a ticket by ID without authentication.",
)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve a ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# PUBLIC_INTERFACE
@router.put(
    "/{ticket_id}",
    response_model=TicketPublic,
    summary="Update ticket",
    description="Update ticket fields without authentication.",
)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    """Update ticket fields. Public access; no role checks."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if payload.title is not None:
        ticket.title = payload.title
    if payload.description is not None:
        ticket.description = payload.description
    if payload.status is not None:
        ticket.status = payload.status
    if payload.assignee_id is not None:
        ticket.assignee_id = payload.assignee_id

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
