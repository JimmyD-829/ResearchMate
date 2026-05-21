import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def registered_user():
    client.post(
        "/api/auth/register",
        json={"email": "news@example.com", "password": "password123", "nickname": "NewsUser"}
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "news@example.com", "password": "password123"}
    )
    return login_response.json()["access_token"]

def test_follow_company(registered_user):
    response = client.post(
        "/api/follows",
        json={"company_name": "腾讯", "stock_code": "00700"},
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "腾讯"
    assert data["stock_code"] == "00700"
    assert "id" in data

def test_get_follows(registered_user):
    client.post(
        "/api/follows",
        json={"company_name": "阿里巴巴", "stock_code": "BABA"},
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    response = client.get(
        "/api/follows",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["company_name"] == "阿里巴巴"

def test_unfollow_company(registered_user):
    follow_response = client.post(
        "/api/follows",
        json={"company_name": "字节跳动"},
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    follow_id = follow_response.json()["id"]
    
    response = client.delete(
        f"/api/follows/{follow_id}",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 204
    
    get_response = client.get(
        "/api/follows",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert len(get_response.json()) == 0

def test_unfollow_not_found(registered_user):
    response = client.delete(
        "/api/follows/nonexistent-id",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 404
    assert "Follow not found" in response.json()["detail"]

def test_get_news(registered_user):
    response = client.get(
        "/api/news",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
