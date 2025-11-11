import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Auth
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # CORS and environment
    CORS_ALLOW_ORIGINS: Optional[str] = os.getenv("CORS_ALLOW_ORIGINS", "*")  # comma-separated or *
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
    return Settings(
        DATABASE_URL=db_url,
        ENV=os.getenv("REACT_APP_NODE_ENV", "development"),
        SECRET_KEY=os.getenv("SECRET_KEY"),
        ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        CORS_ALLOW_ORIGINS=os.getenv("CORS_ALLOW_ORIGINS", "*"),
    )
