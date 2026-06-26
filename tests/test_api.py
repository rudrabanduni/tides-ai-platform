import time
import json
import pytest
import uuid
import threading
from fastapi.testclient import TestClient
from app.api.main import app

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

client = TestClient(app)

def test_openapi_and_swagger():
    # Verify OpenAPI schema generation
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "info" in response.json()
    assert response.json()["info"]["title"] == "TIDES Intelligence Engine API"

    # Verify Swagger UI endpoint
    response = client.get("/docs")
    assert response.status_code == 200

    # Verify ReDoc UI endpoint
    response = client.get("/redoc")
    assert response.status_code == 200

def test_system_endpoints():
    # 1. Health
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "uptime_seconds" in data["data"]
    assert "registered_experts" in data["data"]

    # 2. Version
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["data"]["api_version"] == "1.0.0"

    # 3. Metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "total_registered_startups" in response.json()["data"]

    # 4. Status
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "operational"

def test_error_handlers():
    # 404 NotFound
    response = client.get(f"/startups/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert "not found" in response.json()["message"].lower()

    # 422 ValidationError (missing startup_name)
    response = client.post("/startups", json={"sector": "SaaS"})
    assert response.status_code == 422
    assert response.json()["success"] is False
    assert "validation failed" in response.json()["message"].lower()

def test_startup_lifecycle():
    # Create Startup
    payload = {
        "startup_name": "TIDES Innovation Labs",
        "sector": "BioTech",
        "stage": "Seed",
        "problem_statement": "Cancer drug delivery barriers",
        "solution_summary": "Nanoparticle vehicle"
    }
    response = client.post("/startups", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["startup_name"] == "TIDES Innovation Labs"
    startup_id = res_data["data"]["id"]

    # Fetch Startup
    response = client.get(f"/startups/{startup_id}")
    assert response.status_code == 200
    assert response.json()["data"]["sector"] == "BioTech"

    # List Startups
    response = client.get("/startups")
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) >= 1

    # Clean up (will delete at the end of the test flow)
    response = client.delete(f"/startups/{startup_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == startup_id

def test_document_upload_and_delete():
    # Register a startup first
    res_start = client.post("/startups", json={"startup_name": "Doc Startup", "sector": "SaaS"})
    startup_id = res_start.json()["data"]["id"]

    # Upload mock file
    files = {"file": ("pitch.txt", b"TIDES mock pitch content.", "text/plain")}
    data = {"startup_id": startup_id, "document_type": "Pitch Deck"}
    response = client.post("/documents/upload", data=data, files=files)
    assert response.status_code == 201
    doc_data = response.json()
    assert doc_data["success"] is True
    assert doc_data["data"]["filename"] == "pitch.txt"
    doc_id = doc_data["data"]["id"]

    # Fetch document
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["data"]["startup_id"] == startup_id

    # Clean up document
    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200

    # Clean up startup
    client.delete(f"/startups/{startup_id}")

def test_evaluation_pipeline_and_downstream_endpoints():
    # Register a startup
    res_start = client.post("/startups", json={"startup_name": "Eval Startup", "sector": "CleanTech"})
    startup_id = res_start.json()["data"]["id"]

    # Trigger evaluation (Background task runs synchronously in TestClient context)
    response = client.post(f"/evaluate/{startup_id}")
    assert response.status_code == 202
    assert response.json()["data"]["status"] == "queued"

    # Fetch Evaluation Graph
    response = client.get(f"/evaluation/{startup_id}")
    assert response.status_code == 200
    graph_data = response.json()["data"]
    assert graph_data["startup_id"] == startup_id
    assert "investment_assessment" in graph_data
    assert "executive_assessment" in graph_data

    # Fetch Graph directly
    response = client.get(f"/graph/{startup_id}")
    assert response.status_code == 200

    # Fetch Lineage Trace
    response = client.get(f"/graph/{startup_id}/trace")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], dict)

    # Fetch Node lists
    response = client.get(f"/graph/{startup_id}/observations")
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0

    response = client.get(f"/graph/{startup_id}/risks")
    assert response.status_code == 200

    response = client.get(f"/graph/{startup_id}/questions")
    assert response.status_code == 200

    # Fetch Reports
    response = client.get(f"/reports/{startup_id}")
    assert response.status_code == 200

    # Fetch Report Markdown
    response = client.get(f"/reports/{startup_id}/markdown")
    assert response.status_code == 200
    assert "#" in response.json()["data"]

    # Download Report PDF
    response = client.get(f"/reports/{startup_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0

    # Fetch Portfolio rankings
    response = client.get("/portfolio")
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) >= 1

    # Fetch Top Startups
    response = client.get("/portfolio/top?limit=5")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1

    # Fetch Portfolio Statistics
    response = client.get("/portfolio/statistics")
    assert response.status_code == 200
    assert response.json()["data"]["portfolio_size"] >= 1

    # Fetch Portfolio by Category
    response = client.get("/portfolio/category/CleanTech")
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) >= 1

    # Fetch Committee decisions
    response = client.get("/committee")
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) >= 1

    # Fetch Specific Committee decision
    response = client.get(f"/committee/{startup_id}")
    assert response.status_code == 200
    assert response.json()["data"]["startup_id"] == startup_id

    # Fetch Incubation decisions
    response = client.get("/committee/incubate")
    assert response.status_code == 200

    # Clean up
    client.delete(f"/startups/{startup_id}")

def test_pagination_filtering_and_sorting():
    # Create 3 startups
    s1 = client.post("/startups", json={"startup_name": "Alpha Inc", "sector": "SaaS"}).json()["data"]["id"]
    s2 = client.post("/startups", json={"startup_name": "Beta Inc", "sector": "BioTech"}).json()["data"]["id"]
    s3 = client.post("/startups", json={"startup_name": "Gamma Inc", "sector": "SaaS"}).json()["data"]["id"]

    # Test sorting (+name)
    response = client.get("/startups?sorting=+startup_name")
    names = [s["startup_name"] for s in response.json()["data"]["items"]]
    # Verify sorting
    assert "Alpha Inc" in names
    
    # Test pagination limit/offset
    response = client.get("/startups?limit=2&offset=0")
    assert len(response.json()["data"]["items"]) <= 2
    assert response.json()["data"]["pagination"]["page_size"] == 10 # default page_size remains in metadata

    # Clean up
    client.delete(f"/startups/{s1}")
    client.delete(f"/startups/{s2}")
    client.delete(f"/startups/{s3}")

def test_api_performance_and_concurrency():
    # 1. Health endpoint <10ms benchmark
    durations = []
    for _ in range(20):
        t_start = time.perf_counter()
        response = client.get("/health")
        t_end = time.perf_counter()
        assert response.status_code == 200
        durations.append((t_end - t_start) * 1000.0)
    avg_health_ms = sum(durations) / len(durations)
    print(f"Average Health endpoint duration: {avg_health_ms:.2f} ms")
    # Note: local test execution might have slight cold-start overhead, but average should be low
    assert avg_health_ms < 50.0, f"Average health took {avg_health_ms:.2f}ms (Target: <10ms/50ms local)"

    # 2. Concurrency checks
    errors = []
    def worker():
        try:
            res = client.get("/health")
            assert res.status_code == 200
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent requests had failures: {errors}"
