import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.users.service import UserService
from app.security.api_keys import api_key_store
from app.security.schemas import APIKeyCreate
from app.core.enums import RoleName


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


def test_api_key_lifecycle() -> None:
    # 1. Create key
    payload = APIKeyCreate(name="Test Key", role=RoleName.VIEWER)
    key_resp = api_key_store.create(payload)
    
    assert key_resp.id is not None
    assert key_resp.name == "Test Key"
    assert key_resp.role == "viewer"
    assert key_resp.key.startswith("tid_")
    
    # 2. Validate key
    validated = api_key_store.validate(key_resp.key)
    assert validated is not None
    assert validated.name == "Test Key"
    assert validated.role == "viewer"
    
    # 3. List keys
    all_keys = api_key_store.list_all()
    assert len(all_keys) > 0
    assert any(k.id == key_resp.id for k in all_keys)
    
    # 4. Revoke key
    revoked = api_key_store.revoke(key_resp.id)
    assert revoked is True
    
    # Validation should fail now
    assert api_key_store.validate(key_resp.key) is None
    
    # 5. Delete key
    deleted = api_key_store.delete(key_resp.id)
    assert deleted is True
    
    # Should not be in list anymore
    assert not any(k.id == key_resp.id for k in api_key_store.list_all())


def test_api_key_endpoint_and_auth(client, db_session) -> None:
    # Bootstrap admin
    user_service = UserService(db_session)
    admin_user = user_service.bootstrap_admin(name="Test Admin", email="admin@tides.ai", password="Password123!!")
    
    from app.core.config import get_settings
    with patch.object(get_settings(), "dev_mode", False):
        # Authenticate admin to manage keys
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@tides.ai", "password": "Password123!!"},
        )
        assert login_res.status_code == 200
        access_token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        
        # 1. Create API key via endpoint
        key_create_res = client.post(
            "/api/v1/apikeys",
            json={"name": "Client Key", "role": "admin"},
            headers=auth_headers,
        )
        assert key_create_res.status_code == 201
        key_data = key_create_res.json()
        raw_key = key_data["key"]
        key_id = key_data["id"]
        
        # 2. Get API keys list via endpoint
        key_list_res = client.get("/api/v1/apikeys", headers=auth_headers)
        assert key_list_res.status_code == 200
        assert len(key_list_res.json()) > 0
        
        # 3. Use API Key to access a protected endpoint (e.g. GET /auth/me)
        key_headers = {"X-API-Key": raw_key}
        me_res = client.get("/api/v1/auth/me", headers=key_headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "admin@tides.ai"
        
        # 4. Delete API Key via endpoint
        del_res = client.delete(f"/api/v1/apikeys/{key_id}", headers=auth_headers)
        assert del_res.status_code == 200
        
        # 5. Access again (should fail)
        me_res_blocked = client.get("/api/v1/auth/me", headers=key_headers)
        assert me_res_blocked.status_code == 401
