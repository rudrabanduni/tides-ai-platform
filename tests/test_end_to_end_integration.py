import os
import io
import tempfile
import base64
import pytest
import uuid
import json
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.api.main import app
from app.db.session import get_db
from app.modules.documents.models import Document
from app.modules.intelligence.models import StartupClaim, StartupEvidence
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.modules.evaluation.graph.graph_models import NodeType
from app.modules.evaluation.graph.graph_serializer import from_json as graph_from_json

@pytest.fixture(autouse=True)
def mock_auth():
    from app.security.auth import get_current_user
    from types import SimpleNamespace
    
    fake_admin = SimpleNamespace(
        id=uuid.uuid4(),
        is_active=True,
        role=SimpleNamespace(name="admin"),
    )
    
    app.dependency_overrides[get_current_user] = lambda: fake_admin
    yield
    app.dependency_overrides.clear()

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

def test_end_to_end_pipeline_integration(test_client, db_session):
    # 1. Create a temporary PDF file containing clean energy startup facts
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        c = canvas.Canvas(tmp_path)
        c.drawString(100, 750, "Company: CleanEnergy Corp.")
        c.drawString(100, 730, "Founders: John Doe, Jane Smith.")
        c.drawString(100, 710, "Leadership experience: Founders have 15 years of industry experience.")
        c.drawString(100, 690, "Domain expertise: Core competency in hydrogen fuel cells and clean technology.")
        c.drawString(100, 670, "Commitment: The team is committed full-time.")
        c.drawString(100, 650, "Product: Modular hydrogen fuel cells for backup industrial power.")
        c.drawString(100, 630, "Problem: Industrial power grid outages cost billions.")
        c.drawString(100, 610, "Value proposition: Provides clean, 99.999% reliable backup power.")
        c.drawString(100, 590, "Customers: Grid utility companies and datacenter operators.")
        c.drawString(100, 570, "Business model: Hardware sales plus annual maintenance contracts.")
        c.drawString(100, 550, "Market: Clean energy storage and backup power market.")
        c.drawString(100, 530, "Market size: Total addressable market is $12 Billion globally.")
        c.drawString(100, 510, "Competitors: Legacy diesel generators and hydrogen battery rivals.")
        c.drawString(100, 490, "Competition analysis: Hydrogen fuel cells are 50% more efficient than rivals.")
        c.drawString(100, 470, "Revenue model: High margin hardware sales.")
        c.drawString(100, 450, "Funding received: Raised $2.5 Million in seed funding.")
        c.drawString(100, 430, "Current revenue: Revenue is $0.0 ARR.")
        c.drawString(100, 410, "Financial metrics: High gross margins expected.")
        c.drawString(100, 390, "Technology description: Proprietary hydrogen fuel cell stack.")
        c.drawString(100, 370, "TRL level: TRL 6 readiness level validated in pilot.")
        c.drawString(100, 350, "IP status: Two patents filed for cell stack design.")
        c.drawString(100, 330, "Risks: Market adoption risk, regulatory certification risk, supply chain risk.")
        c.save()
        
        # 2. Read the PDF bytes
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
            
        # 3. Call the POST /evaluate-startup endpoint with the PDF
        response = test_client.post(
            "/evaluate-startup",
            data={
                "startup_name": "CleanEnergy Corp",
                "sector": "CleanTech",
                "stage": "Seed"
            },
            files={
                "files": ("clean_energy_deck.pdf", pdf_bytes, "application/pdf")
            }
        )
        
        # Fallback to api prefix if standard fails
        if response.status_code == 404:
            response = test_client.post(
                "/api/v1/evaluate-startup",
                data={
                    "startup_name": "CleanEnergy Corp",
                    "sector": "CleanTech",
                    "stage": "Seed"
                },
                files={
                    "files": ("clean_energy_deck.pdf", pdf_bytes, "application/pdf")
                }
            )
            
        assert response.status_code == 201
        res_data = response.json()["data"]
        assert res_data["evaluation_status"] == "COMPLETED"
        assert "assessment_identifier" in res_data
        assert "generated_report" in res_data
        assert "pdf_base64" in res_data
        
        # Verify no "Mock" string exists in the generated report
        report_str = json.dumps(res_data["generated_report"])
        print(f"REPORT STR: {report_str}")
        assert "mock" not in report_str.lower()
        
        # Verify the report contains real observations from the PDF
        assert "hydrogen" in report_str or "Hydrogen" in report_str
        assert "John Doe" in report_str or "Jane Smith" in report_str
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
