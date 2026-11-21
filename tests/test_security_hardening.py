"""Security hardening, auth separation, path validation, upload hygiene & PII sanitization tests."""
from __future__ import annotations

import json
import os
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.api.dependencies import EvaluationService
from app.api.exceptions import EvaluationNotFoundError, setup_exception_handlers
from app.core.config import get_settings
from app.core.enums import DocumentType, RoleName
from app.core.exceptions import ValidationError
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.auth.dependencies import EvaluatorUser
from app.modules.documents.service import DocumentService
from app.modules.intelligence.service import IntelligenceService
from app.modules.startups.schemas import StartupCreate
from app.modules.startups.service import StartupService
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService
from app.security.api_keys import api_key_store
from app.security.schemas import APIKeyCreate


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
def client(db_session: Session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_api_key_never_escalates_role(client: TestClient, db_session: Session) -> None:
    """A viewer API key must never fall back to an active admin user."""
    user_service = UserService(db_session)
    user_service.bootstrap_admin(name="Admin", email="admin@tides.ai", password="Password123!!")

    viewer_key = api_key_store.create(APIKeyCreate(name="Viewer Only Key", role=RoleName.VIEWER))
    try:
        with patch.object(get_settings(), "dev_mode", False):
            res = client.get("/api/v1/auth/me", headers={"X-API-Key": viewer_key.key})
            assert res.status_code == 401
    finally:
        api_key_store.delete(viewer_key.id)


def test_jwt_access_and_refresh_type_separation(client: TestClient, db_session: Session) -> None:
    """Access tokens must fail on /auth/refresh and refresh tokens must fail as Bearer auth."""
    UserService(db_session).bootstrap_admin(name="Admin", email="admin@tides.ai", password="Password123!!")

    with patch.object(get_settings(), "dev_mode", False):
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@tides.ai", "password": "Password123!!"},
        )
        assert login_res.status_code == 200
        tokens = login_res.json()

        # Refresh token rejected as Bearer access token
        me_with_refresh = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert me_with_refresh.status_code == 401

        # Access token rejected at /auth/refresh
        refresh_with_access = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["access_token"]},
        )
        assert refresh_with_access.status_code == 401


def test_routers_require_authentication_when_dev_mode_disabled(client: TestClient) -> None:
    """Protected platform routes return 401 unauthenticated while system health stays public."""
    uid = str(uuid4())
    with patch.object(get_settings(), "dev_mode", False):
        assert client.get("/health").status_code == 200
        assert client.get("/version").status_code == 200
        assert client.get("/status").status_code == 200

        protected_gets = [
            "/startups",
            "/portfolio",
            "/committee",
            f"/evaluation/{uid}",
            f"/reports/{uid}",
            f"/graph/{uid}",
            f"/documents/{uid}",
        ]
        for path in protected_gets:
            resp = client.get(path)
            assert resp.status_code == 401, f"{path} returned {resp.status_code} unauthenticated"

        resp_intake = client.post(
            "/api/v1/intake/upload-applications",
            files={
                "file": (
                    "apps.xlsx",
                    b"dummy",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert resp_intake.status_code == 401


def test_path_traversal_and_header_injection_rejected(client: TestClient, db_session: Session) -> None:
    """Path traversal identifiers return 422/EvaluationNotFoundError and never escape graphs_dir."""
    eval_service = EvaluationService(db_session)
    with pytest.raises(EvaluationNotFoundError):
        eval_service._get_graph_path("../secret")
    with pytest.raises(EvaluationNotFoundError):
        eval_service._get_graph_path("..\\secret")

    UserService(db_session).bootstrap_admin(name="Admin", email="admin@tides.ai", password="Password123!!")
    with patch.object(get_settings(), "dev_mode", False):
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@tides.ai", "password": "Password123!!"},
        )
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # Non-UUID startup ID on evaluation endpoint -> 422
        assert client.get("/evaluation/not-a-uuid", headers=headers).status_code == 422
        # Unsafe pattern on reports endpoint (percent-encoded dot / whitespace / quotes) -> 422
        assert client.get("/reports/bad..id", headers=headers).status_code == 422


def test_document_upload_extension_empty_and_filename_sanitization(db_session: Session, tmp_path: Path) -> None:
    """DocumentService rejects bad extensions and empty files, and strips Windows/POSIX path traversal."""
    startup = StartupService(db_session).create(
        StartupCreate(
            startup_name="SecureVenture",
            sector="DeepTech",
            stage="Seed",
            problem_statement="P",
            solution_summary="S",
            business_model="B2B",
            target_market="Enterprise",
        ),
        actor_id=None,
    )
    doc_service = DocumentService(db_session)

    with patch.object(get_settings(), "upload_dir", str(tmp_path)):
        # Unsupported executable extension
        bad_file = StarletteUploadFile(filename="payload.exe", file=BytesIO(b"MZ"))
        with pytest.raises(ValidationError):
            doc_service.upload(startup.id, file=bad_file, document_type=DocumentType.OTHER, actor_id=None)

        # Empty 0-byte PDF
        empty_file = StarletteUploadFile(filename="empty.pdf", file=BytesIO(b""))
        with pytest.raises(ValidationError):
            doc_service.upload(startup.id, file=empty_file, document_type=DocumentType.PITCH_DECK, actor_id=None)

        # Windows-style traversal filename gets stripped to basename cleanly
        valid_file = StarletteUploadFile(filename="..\\..\\deck.txt", file=BytesIO(b"Clean pitch deck"))
        doc = doc_service.upload(startup.id, file=valid_file, document_type=DocumentType.PITCH_DECK, actor_id=None)
        assert doc.original_filename == "deck.txt"
        assert Path(doc.file_path).resolve().parent == (tmp_path / str(startup.id)).resolve()


def test_intake_size_limit_and_extension_enforced(client: TestClient, db_session: Session) -> None:
    """Intake route enforces .xlsx extension and max_upload_size_mb ceiling before parsing."""
    UserService(db_session).bootstrap_admin(name="Admin", email="admin@tides.ai", password="Password123!!")
    with patch.object(get_settings(), "dev_mode", False):
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@tides.ai", "password": "Password123!!"},
        )
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        bad_ext = client.post(
            "/api/v1/intake/upload-applications",
            headers=headers,
            files={"file": ("apps.csv", b"col1,col2\n", "text/csv")},
        )
        assert bad_ext.status_code == 422

        with patch.object(get_settings(), "max_upload_size_mb", 0):
            oversized = client.post(
                "/api/v1/intake/upload-applications",
                headers=headers,
                files={
                    "file": (
                        "apps.xlsx",
                        b"exceeds zero mb limit",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )
            assert oversized.status_code == 422


def test_internal_error_masks_exception_details_in_production() -> None:
    """Unhandled 500 handler must mask raw exception text when debug and dev_mode are False."""
    test_app = FastAPI()
    setup_exception_handlers(test_app)

    @test_app.get("/boom")
    def _boom():
        raise RuntimeError("sensitive_db_password=super_secret_token")

    with patch.object(get_settings(), "debug", False), patch.object(get_settings(), "dev_mode", False):
        tc = TestClient(test_app, raise_server_exceptions=False)
        resp = tc.get("/boom")
        assert resp.status_code == 500
        body = resp.json()
        assert "super_secret_token" not in body["message"]
        assert "super_secret_token" not in body["detail"]
        assert "request_id" in body


def test_intelligence_sidecar_sanitizes_metadata_and_tables(db_session: Session, tmp_path: Path) -> None:
    """IntelligenceService must sanitize PII inside sidecar .meta.json title, author, and tables."""
    import openpyxl

    startup = StartupService(db_session).create(
        StartupCreate(
            startup_name="PII CleanTest",
            sector="SaaS",
            stage="Seed",
            problem_statement="P",
            solution_summary="S",
            business_model="B2B",
            target_market="Enterprise",
        ),
        actor_id=None,
    )

    wb = openpyxl.Workbook()
    wb.properties.title = "Deck by founder.secret@example.com"
    wb.properties.creator = "Jane +91-9876543210"
    ws = wb.active
    ws.append(["Founder Email", "Phone"])
    ws.append(["founder.secret@example.com", "+91-9876543210"])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    with patch.object(get_settings(), "upload_dir", str(tmp_path)):
        upload = StarletteUploadFile(filename="roster.xlsx", file=buf)
        doc = DocumentService(db_session).upload(
            startup.id,
            file=upload,
            document_type=DocumentType.COMPANY_DOCUMENT,
            actor_id=None,
        )
        meta = IntelligenceService(db_session).process_document(doc.id)
        serialized = json.dumps(meta)
        assert "founder.secret@example.com" not in serialized
        assert "9876543210" not in serialized
        meta_disk = Path(doc.file_path + ".meta.json").read_text(encoding="utf-8")
        assert "founder.secret@example.com" not in meta_disk
        assert "9876543210" not in meta_disk


def test_role_rbac_allows_incubation_manager_and_analyst(client: TestClient, db_session: Session) -> None:
    """Incubation Manager and Analyst roles pass EvaluatorUser/ReadOnlyUser checks while Viewer is blocked from evaluator routes."""
    service = UserService(db_session)
    admin = service.bootstrap_admin(name="Admin", email="admin@tides.ai", password="Password123!!")
    service.create_user(
        UserCreate(name="IncMgr", email="incmgr@tides.ai", password="Password123!!", role=RoleName.INCUBATION_MANAGER),
        actor_id=admin.id,
    )
    service.create_user(
        UserCreate(name="Analyst", email="analyst@tides.ai", password="Password123!!", role=RoleName.ANALYST),
        actor_id=admin.id,
    )
    service.create_user(
        UserCreate(name="Viewer", email="viewer@tides.ai", password="Password123!!", role=RoleName.VIEWER),
        actor_id=admin.id,
    )

    def _login(email: str) -> dict[str, str]:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!!"})
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    with patch.object(get_settings(), "dev_mode", False):
        incmgr_headers = _login("incmgr@tides.ai")
        analyst_headers = _login("analyst@tides.ai")
        viewer_headers = _login("viewer@tides.ai")

        # ReadOnlyUser allows all three roles
        for hdrs in (incmgr_headers, analyst_headers, viewer_headers):
            assert client.get("/startups", headers=hdrs).status_code == 200

        # EvaluatorUser allows Incubation Manager & Analyst (validation error 400/422, not 401/403), blocks Viewer (403)
        dummy_file = {"file": ("bad.txt", b"not-xlsx", "text/plain")}
        assert client.post("/api/v1/intake/upload-applications", files=dummy_file, headers=viewer_headers).status_code == 403
        assert client.post("/api/v1/intake/upload-applications", files=dummy_file, headers=incmgr_headers).status_code in (400, 422)
        assert client.post("/api/v1/intake/upload-applications", files=dummy_file, headers=analyst_headers).status_code in (400, 422)


def test_evaluate_startup_requires_authentication(client: TestClient) -> None:
    """POST /evaluate-startup fails closed (401) without authentication."""
    with patch.object(get_settings(), "dev_mode", False):
        resp = client.post(
            "/evaluate-startup",
            data={"startup_name": "NoAuth Co", "sector": "SaaS", "stage": "Seed"},
            files={"files": ("deck.txt", b"pitch content", "text/plain")},
        )
        assert resp.status_code == 401


def test_evaluation_service_ignores_sidecar_and_report_aliases(db_session: Session, tmp_path: Path) -> None:
    """EvaluationService skips .metadata.json, REPORT-*.json, portfolio.json, and dotfiles while resolving report aliases."""
    from app.modules.evaluation.graph.mock_graph import create_fallback_observation_graph
    from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine

    sid = str(uuid4())
    graph = DueDiligenceReportEngine.generate(
        create_fallback_observation_graph(
            startup_id=sid,
            name="CleanFilter Co",
            category="CleanTech",
            investment_score=74.0,
            confidence=0.85,
        )
    )
    report_id = graph.report.report_id
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(get_settings(), "upload_dir", str(tmp_path)):
        svc = EvaluationService(db_session)
        svc.save_graph(graph)
        # Sidecar & alias files that must not corrupt get_all_graphs() or save_graph() loops
        (graphs_dir / f"{sid}.metadata.json").write_text(json.dumps({"cost_observability": {"startup_id": sid}}), encoding="utf-8")
        (graphs_dir / f"{report_id}.json").write_text((graphs_dir / f"{sid}.json").read_text(encoding="utf-8"), encoding="utf-8")
        (graphs_dir / "portfolio.json").write_text(json.dumps({"portfolio_id": "PORT-1"}), encoding="utf-8")
        (graphs_dir / ".json").write_text(json.dumps({"startup_id": ""}), encoding="utf-8")

        assert svc.list_evaluated_startups() == [sid]
        all_graphs = svc.get_all_graphs()
        assert len(all_graphs) == 1
        assert all_graphs[0].startup_id == sid
        assert svc.get_graph(report_id).startup_id == sid


