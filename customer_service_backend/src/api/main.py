from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.session import Base, engine

app = FastAPI(
    title="Customer Service Backend",
    description="APIs for user management, ticketing, and messaging.",
    version="0.1.0",
    openapi_tags=[
        {"name": "health", "description": "Service health and diagnostics"},
        {"name": "users", "description": "User-related operations"},
        {"name": "tickets", "description": "Ticket management operations"},
        {"name": "messages", "description": "Ticket message operations"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can be restricted via env in future
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize database tables on application startup."""
    Base.metadata.create_all(bind=engine)


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check", description="Simple health check endpoint.")
def health_check():
    """Health check endpoint for readiness probes.

    Returns:
        dict: A JSON payload with message field.
    """
    return {"message": "Healthy"}
