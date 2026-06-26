import pytest
import concurrent.futures
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.users.service import UserService
from app.security.jwt import jwt_service
from app.security.audit import get_recent_events, clear_audit_ring


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_security_headers(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    
    headers = response.headers
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert "Strict-Transport-Security" in headers
    assert "Referrer-Policy" in headers
    assert "Permissions-Policy" in headers


def test_audit_logging_events(client, db_session) -> None:
    clear_audit_ring()
    
    # 1. Trigger failed login
    from app.core.config import get_settings
    with patch.object(get_settings(), "dev_mode", False):
        client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@tides.ai", "password": "BadPassword123!"},
        )
        
        events = get_recent_events(limit=10)
        assert len(events) > 0
        
        # Check that we logged a login failure
        failure_event = [e for e in events if e.action == "security.login_failure"]
        assert len(failure_event) > 0
        assert failure_event[0].actor == "wrong@tides.ai"
        assert failure_event[0].status == "failure"


def test_concurrent_jwt_operations() -> None:
    user_id = "12345678-1234-1234-1234-1234567890ab"
    role = "admin"
    
    def run_token_lifecycle():
        token = jwt_service.create_access_token(user_id, role)
        claims = jwt_service.decode_token(token)
        return claims is not None and claims.subject == user_id
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_token_lifecycle) for _ in range(50)]
        results = [f.result() for f in futures]
        
    assert all(results) is True
