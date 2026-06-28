import os
import pytest
import io
import base64
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api.main import app
from app.db.session import get_db
from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline

@pytest.fixture()
def db_session() -> Session:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base

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
def test_client(db_session: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.mark.anyio
async def test_coordinate_evaluation_pipeline(db_session: Session):
    # Prepare dummy files
    dummy_file_content = b"This is a pitch deck text for MockStartup. Founders: Alice Smith, Bob Jones. Problem: Manual analysis is slow. Solution: AI startup analyst. Market: VCs."
    file_like = io.BytesIO(dummy_file_content)
    
    class DummyUploadFile:
        def __init__(self, filename, content):
            self.filename = filename
            self.file = io.BytesIO(content)
            self.content_type = "text/plain"
            
        async def read(self, *args, **kwargs):
            return self.file.read()
            
    uploaded_files = [DummyUploadFile("deck.txt", dummy_file_content)]

    # Run pipeline
    result = await coordinate_evaluation_pipeline(
        db=db_session,
        startup_name="MockStartup Inc",
        sector="Artificial Intelligence",
        stage="Pre-Seed",
        files=uploaded_files
    )

    assert result["evaluation_status"] == "COMPLETED"
    assert "assessment_identifier" in result
    assert "generated_report" in result
    assert "pdf_url" in result
    assert "pdf_base64" in result

    # Validate PDF decode
    pdf_bytes = base64.b64decode(result["pdf_base64"])
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")

def test_api_evaluate_startup_endpoint(test_client: TestClient):
    # Simulate multi-part file upload
    file_data = ("deck.txt", b"MockStartup deck. Founders: Alice, Bob.", "text/plain")
    
    response = test_client.post(
        "/evaluate-startup",
        data={
            "startup_name": "API MockStartup",
            "sector": "SaaS",
            "stage": "Seed"
        },
        files={
            "files": file_data
        }
    )
    
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["message"] == "Startup evaluated successfully end-to-end"
    
    data = json_data["data"]
    assert data["evaluation_status"] == "COMPLETED"
    assert "assessment_identifier" in data
    assert "generated_report" in data
    assert "pdf_url" in data
    assert "pdf_base64" in data
