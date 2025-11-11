from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.db.session import Base, engine
from src.api.routers_auth import router as auth_router
from src.api.routers_users import router as users_router
from src.api.routers_tickets import router as tickets_router
from src.api.routers_messages import router as messages_router

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

settings = get_settings()
allow_origins = ["*"]
if settings.CORS_ALLOW_ORIGINS and settings.CORS_ALLOW_ORIGINS != "*":
    allow_origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tickets_router)
app.include_router(messages_router)


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
