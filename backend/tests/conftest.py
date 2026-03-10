"""
Test configuration and shared fixtures.

Patches heavy optional dependencies (pgvector, sentence_transformers, ollama)
so tests run without GPU or a live database/Ollama instance.
Uses an in-memory SQLite DB for fast, isolated integration tests.
"""
import sys
from unittest.mock import MagicMock, patch
import sqlalchemy as sa

# ── Patch pgvector before any app import ────────────────────────────────────
_mock_pgvector_sa = MagicMock()
_mock_pgvector_sa.Vector = lambda dim: sa.Text()  # store as Text in SQLite
sys.modules.setdefault("pgvector", MagicMock())
sys.modules["pgvector.sqlalchemy"] = _mock_pgvector_sa

# ── Patch sentence_transformers ──────────────────────────────────────────────
_mock_st = MagicMock()
_mock_st.SentenceTransformer.return_value.encode.return_value = [0.0] * 768
sys.modules.setdefault("sentence_transformers", _mock_st)

# ── Patch ollama / langchain-ollama ──────────────────────────────────────────
sys.modules.setdefault("ollama", MagicMock())
sys.modules.setdefault("langchain_ollama", MagicMock())
sys.modules.setdefault("langchain_community", MagicMock())
sys.modules.setdefault("langgraph", MagicMock())

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

import app.database as _db_module
from app.main import app
from app.database import get_session
from app.models.db import User
from app.core.security import get_password_hash, create_access_token

TEST_DB_URL = "sqlite://"


@pytest.fixture(name="engine", scope="function")
def engine_fixture():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Redirect the module-level engine so on_startup creates tables in SQLite
    original_engine = _db_module.engine
    _db_module.engine = engine
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    _db_module.engine = original_engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="user")
def user_fixture(session):
    """A registered user in the DB."""
    u = User(email="test@example.com", password_hash=get_password_hash("password123"))
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(user):
    """Bearer token headers for the test user."""
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}
