import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine
import tempfile
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def registered_user():
    response = client.post(
        "/api/auth/register",
        json={"email": "report@example.com", "password": "password123", "nickname": "ReportUser"}
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "report@example.com", "password": "password123"}
    )
    return login_response.json()["access_token"]

def test_upload_report(registered_user):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 test content")
        f.flush()
        
        response = client.post(
            "/api/reports",
            files={"file": ("test.pdf", open(f.name, "rb"), "application/pdf")},
            headers={"Authorization": f"Bearer {registered_user}"}
        )
        
        os.unlink(f.name)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["company_name"] is not None

def test_upload_non_pdf(registered_user):
    response = client.post(
        "/api/reports",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_get_reports(registered_user):
    response = client.get(
        "/api/reports",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_report_not_found(registered_user):
    response = client.get(
        "/api/reports/nonexistent-id",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 404
    assert "Report not found" in response.json()["detail"]
