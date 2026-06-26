import pytest
from datetime import timedelta
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


def test_jwt_generation_and_validation() -> None:
    # 1. Access token
    user_id = "12345678-1234-1234-1234-1234567890ab"
    role = "admin"
    token = jwt_service.create_access_token(user_id, role)
    assert token is not None
    assert isinstance(token, str)

    # 2. Decode claims
    claims = jwt_service.decode_token(token)
    assert claims is not None
    assert claims.subject == user_id
    assert claims.role == role

    # 3. Decode token data
    token_data = jwt_service.decode_token_data(token)
    assert token_data is not None
    assert token_data.user_id == user_id
    assert token_data.role == role


def test_jwt_expired() -> None:
    user_id = "12345678-1234-1234-1234-1234567890ab"
    role = "viewer"
    
    # Generate token that is already expired
    token = jwt_service.create_access_token(user_id, role, expires_delta=timedelta(seconds=-10))
    
    # Validation should fail (clock skew leeway is 30s, so -10s is within leeway!)
    # Wait, let's check with -60s so it's outside the clock skew leeway!
    token_expired = jwt_service.create_access_token(user_id, role, expires_delta=timedelta(seconds=-60))
    
    claims = jwt_service.decode_token(token_expired)
    assert claims is None


def test_jwt_blacklist() -> None:
    user_id = "12345678-1234-1234-1234-1234567890ab"
    role = "admin"
    token = jwt_service.create_access_token(user_id, role)
    claims = jwt_service.decode_token(token)
    assert claims is not None
    
    # Revoke
    jwt_service.revoke_token(claims.jti)
    assert jwt_service.is_revoked(claims.jti)
    
    # Decoding should fail now
    assert jwt_service.decode_token(token) is None


def test_login_logout_refresh_flow(client, db_session) -> None:
    # 1. Bootstrap admin
    user_service = UserService(db_session)
    admin_user = user_service.bootstrap_admin(name="Test Admin", email="admin@tides.ai", password="Password123!!")
    
    # Disable DEV_MODE during the test to enforce token verification
    from app.core.config import get_settings
    with patch.object(get_settings(), "dev_mode", False):
        # 2. Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@tides.ai", "password": "Password123!!"},
        )
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 3. Access protected route with access token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_res = client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "admin@tides.ai"
        
        # 4. Refresh token
        refresh_res = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 200
        new_tokens = refresh_res.json()
        assert "access_token" in new_tokens
        
        new_access_token = new_tokens["access_token"]
        
        # 5. Access protected route with new access token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_res = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_res.status_code == 200
        
        # 6. Logout
        logout_res = client.post("/api/v1/auth/logout", headers=new_headers)
        assert logout_res.status_code == 200
        
        # 7. Access protected route again (should fail because access token is blacklisted)
        me_res_blocked = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_res_blocked.status_code == 401
