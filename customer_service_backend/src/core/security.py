from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.db.models import User
from src.db.session import Session, get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bcrypt limitation: only first 72 bytes are considered. We enforce/guard this.
_BCRYPT_MAX_BYTES = 72

# OAuth2 scheme for FastAPI security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData(BaseModel):
    """JWT token data payload."""
    sub: str = Field(..., description="User email as subject")
    exp: int = Field(..., description="Expiration timestamp (epoch seconds)")
    is_agent: bool = Field(..., description="Whether the user is an agent")
    user_id: int = Field(..., description="User ID")


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed value.

    Notes:
        Bcrypt silently ignores bytes beyond 72. To avoid false positives and
        passlib ValueErrors, we guard inputs:
        - If password bytes > 72, return False rather than verifying a truncated value.
    """
    if plain_password is None:
        return False
    try:
        pw_bytes = plain_password.encode("utf-8")
    except Exception:
        return False
    if len(pw_bytes) > _BCRYPT_MAX_BYTES:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # If the stored hash is invalid/corrupted, treat as non-match
        return False


# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Hash a plain password for storage.

    Behavior:
        - Enforces bcrypt's 72-byte input limit. If exceeded, raise HTTP 422 to prompt client correction.
    """
    if password is None:
        raise HTTPException(status_code=422, detail="Password required")
    try:
        pw_bytes = password.encode("utf-8")
    except Exception:
        raise HTTPException(status_code=422, detail="Password encoding error")
    if len(pw_bytes) > _BCRYPT_MAX_BYTES:
        raise HTTPException(status_code=422, detail="Password too long for bcrypt (max 72 bytes)")
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def create_access_token(
    data: dict,
    secret_key: Optional[str] = None,
    expires_minutes: Optional[int] = None,
    algorithm: str = "HS256",
) -> str:
    """Create a JWT access token with expiration.

    Args:
        data: Claims to include (must include 'sub').
        secret_key: Optionally override secret key from env.
        expires_minutes: Expiration minutes override.
        algorithm: JWT signing algorithm (default: HS256).

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()
    if "sub" not in to_encode:
        raise ValueError("JWT token must include 'sub' claim (subject)")

    expire_minutes = expires_minutes or int(
        (getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", None) or 60)
    )
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": int(expire.timestamp())})
    key = secret_key or getattr(settings, "SECRET_KEY", None)
    if not key:
        raise RuntimeError("SECRET_KEY is not set. Please configure environment.")
    return jwt.encode(to_encode, key, algorithm=algorithm)


# PUBLIC_INTERFACE
def decode_token(token: str) -> TokenData:
    """Decode a JWT token and return TokenData.

    Raises:
        HTTPException: if token is invalid or expired.
    """
    settings = get_settings()
    key = getattr(settings, "SECRET_KEY", None)
    if not key:
        raise HTTPException(status_code=500, detail="Auth not configured")
    try:
        payload = jwt.decode(token, key, algorithms=["HS256"])
        return TokenData(**payload)  # type: ignore[arg-type]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# PUBLIC_INTERFACE
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to get the current authenticated user from JWT."""
    token_data = decode_token(token)
    user = db.query(User).filter(User.id == token_data.user_id, User.email == token_data.sub).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive or missing user")
    return user


# PUBLIC_INTERFACE
def require_agent(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user is an agent."""
    if not user.is_agent:
        raise HTTPException(status_code=403, detail="Agent role required")
    return user


# PUBLIC_INTERFACE
def try_auth_optional(token: Optional[str]) -> Tuple[Optional[User], Optional[TokenData]]:
    """Helper for optional auth scenarios. Not wired to FastAPI directly."""
    if not token:
        return None, None
    try:
        data = decode_token(token)
        return None, data
    except HTTPException:
        return None, None
