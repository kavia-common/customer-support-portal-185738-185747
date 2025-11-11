import os
import sys
import pytest
from typing import Dict

# Ensure 'src' is importable irrespective of pytest working directory.
# Add the backend root (which contains the 'src' package) to sys.path early.
# Dev note: Run test suite with "PYTHONPATH=./src pytest -q" to avoid import path issues.
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.api.main import app
from src.db.session import Base, get_db

# Configure environment for tests
TEST_DB_URL = "sqlite:///./test.db"  # file-backed sqlite to persist across sessions in same process
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

# Build an engine and session factory specific to tests
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the application dependency to use the test database
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _register_user(client: TestClient, email: str, password: str = "password123", is_agent: bool = False):
    res = client.post("/auth/register", json={"email": email, "password": password, "full_name": None, "is_agent": is_agent})
    assert res.status_code == 200, res.text
    token = res.json().get("access_token")
    assert token
    return token


@pytest.fixture
def customer_token(client: TestClient) -> str:
    return _register_user(client, "customer@example.com", is_agent=False)


@pytest.fixture
def agent_token(client: TestClient) -> str:
    return _register_user(client, "agent@example.com", is_agent=True)


@pytest.fixture
def auth_headers_customer(customer_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture
def auth_headers_agent(agent_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {agent_token}"}
