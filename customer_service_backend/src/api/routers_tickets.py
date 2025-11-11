from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.models import Ticket, User
from src.db.schemas import TicketCreate, TicketPublic, TicketUpdate
from src.db.session import get_db

router = APIRouter(prefix="/tickets", tags=["tickets"])


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=TicketPublic,
    summary="Create ticket",
    description="Create a support ticket. The creator is the authenticated user (customer or agent).",
)
def create_ticket(payload: TicketCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new support ticket."""
    if not current.is_agent and payload.creator_id != current.id:
        raise HTTPException(status_code=403, detail="Cannot create ticket for other users")
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
    description="List tickets. Agents see all; customers see only their own.",
)
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List tickets with RBAC and optional status filter."""
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    if not current.is_agent:
        q = q.filter(Ticket.creator_id == current.id)
    return q.order_by(Ticket.created_at.desc()).all()


# PUBLIC_INTERFACE
@router.get(
    "/{ticket_id}",
    response_model=TicketPublic,
    summary="Get ticket by ID",
    description="Retrieve a ticket by ID. Customers must own it; agents can view any.",
)
def get_ticket(ticket_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve a ticket with RBAC."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not current.is_agent and ticket.creator_id != current.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    return ticket


# PUBLIC_INTERFACE
@router.put(
    "/{ticket_id}",
    response_model=TicketPublic,
    summary="Update ticket",
    description="Update ticket fields. Agents can update any; customers can update only title/description on their own tickets.",
)
def update_ticket(ticket_id: int, payload: TicketUpdate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update ticket respecting role-based constraints."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current.is_agent and ticket.creator_id != current.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this ticket")

    # Customers: cannot change status or assignee
    if not current.is_agent:
        if payload.status is not None or payload.assignee_id is not None:
            raise HTTPException(status_code=403, detail="Not allowed to change status/assignee")

    if payload.title is not None:
        ticket.title = payload.title
    if payload.description is not None:
        ticket.description = payload.description
    if current.is_agent:
        if payload.status is not None:
            ticket.status = payload.status
        if payload.assignee_id is not None:
            ticket.assignee_id = payload.assignee_id

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
