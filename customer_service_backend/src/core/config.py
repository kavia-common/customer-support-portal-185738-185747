import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # CORS and environment can be extended later
    ENV: Optional[str] = os.getenv("REACT_APP_NODE_ENV", "development")


@lru_cache()
# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Get cached Settings loaded from environment variables.

    Returns:
        Settings: Configuration values for the application.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Some environments may only expose REACT-like envs; default to local sqlite
        db_url = "sqlite:///./app.db"
    return Settings(DATABASE_URL=db_url, ENV=os.getenv("REACT_APP_NODE_ENV", "development"))
