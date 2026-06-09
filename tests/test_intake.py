from collections.abc import Generator
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.auth.dependencies import get_current_user
from app.modules.founders.models import Founder
from app.modules.intake.service import ExcelIntakeService, normalize_cell, normalize_header
from app.modules.startup_profiles.models import StartupProfile, StartupProfileVersion
from app.modules.startups.models import StartupApplication


EXPECTED_HEADERS = [
    "Startup Name",
    "Founder Name",
    "Founder Email",
    "Problem Statement",
    "Solution",
    "Target Market",
    "Startup Stage",
]


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    fake_user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        role=SimpleNamespace(name="admin"),
    )

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def workbook_bytes(rows: list[list[str | None]], headers: list[str] | None = None) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers or EXPECTED_HEADERS)
    for row in rows:
        worksheet.append(row)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_header_and_cell_normalization() -> None:
    assert normalize_header("  Startup   Name ") == "startup name"
    assert normalize_header(None) == ""
    assert normalize_cell("  Example Startup  ") == "Example Startup"
    assert normalize_cell("   ") is None
    assert normalize_cell(None) is None


def test_upload_applications_imports_valid_rows_and_reports_errors(
    client: TestClient,
    db_session: Session,
) -> None:
    content = workbook_bytes(
        [
            [
                "BatteryX",
                "Asha Rao",
                "asha@example.com",
                "Grid storage is expensive",
                "Affordable battery analytics",
                "Industrial energy users",
                "MVP",
            ],
            [None, None, None, None, None, None, None],
            [
                "NoFounder",
                "",
                "missing-founder@example.com",
                "Problem",
                "Solution",
                "Market",
                "Idea",
            ],
            [
                "DuplicateEmail",
                "Asha Duplicate",
                "asha@example.com",
                "Problem",
                "Solution",
                "Market",
                "Idea",
            ],
        ]
    )

    response = client.post(
        "/api/v1/intake/upload-applications",
        files={
            "file": (
                "applications.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 3
    assert payload["successful_rows"] == 1
    assert payload["failed_rows"] == 2
    assert len(payload["errors"]) == 2
    assert {error["row_number"] for error in payload["errors"]} == {4, 5}

    assert len(db_session.scalars(select(StartupApplication)).all()) == 1
    assert len(db_session.scalars(select(Founder)).all()) == 1
    assert len(db_session.scalars(select(StartupProfile)).all()) == 1
    assert len(db_session.scalars(select(StartupProfileVersion)).all()) == 1

    audit_actions = {log.action for log in db_session.scalars(select(AuditLog)).all()}
    assert "startup_imported_from_excel" in audit_actions
    assert "excel_import_completed" in audit_actions


def test_missing_required_excel_columns_returns_422(client: TestClient) -> None:
    content = workbook_bytes(
        [["BatteryX", "Asha Rao"]],
        headers=["Startup Name", "Founder Name"],
    )

    response = client.post(
        "/api/v1/intake/upload-applications",
        files={"file": ("bad.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 422
    assert "missing required columns" in response.json()["detail"]


def test_duplicate_existing_founder_email_is_rejected(db_session: Session) -> None:
    service = ExcelIntakeService(db_session)
    first_upload = workbook_bytes(
        [
            [
                "BatteryX",
                "Asha Rao",
                "asha@example.com",
                "Grid storage is expensive",
                "Affordable battery analytics",
                "Industrial energy users",
                "MVP",
            ]
        ]
    )
    second_upload = workbook_bytes(
        [
            [
                "BatteryY",
                "Asha Rao",
                "asha@example.com",
                "Another problem",
                "Another solution",
                "Another market",
                "Idea",
            ]
        ]
    )

    first_summary = service.import_applications_from_xlsx(
        filename="first.xlsx",
        content=first_upload,
        actor_id=None,
    )
    second_summary = service.import_applications_from_xlsx(
        filename="second.xlsx",
        content=second_upload,
        actor_id=None,
    )

    assert first_summary.successful_rows == 1
    assert second_summary.successful_rows == 0
    assert second_summary.failed_rows == 1
    assert second_summary.errors[0].message == "Founder Email already exists in the platform"
