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
        json={"email": "emotion@example.com", "password": "password123", "nickname": "EmotionUser"}
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "emotion@example.com", "password": "password123"}
    )
    return login_response.json()["access_token"]

def test_get_emotion_score(registered_user):
    response = client.get(
        "/api/emotion/腾讯",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "腾讯"
    assert "current_score" in data
    assert "current_label" in data
    assert "last_7d_avg" in data
    assert "last_30d_avg" in data

def test_get_emotion_trend(registered_user):
    response = client.get(
        "/api/emotion/阿里巴巴/trend",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "阿里巴巴"
    assert "trend" in data
    assert isinstance(data["trend"], list)

def test_get_emotion_trend_with_days(registered_user):
    response = client.get(
        "/api/emotion/美团/trend?days=7",
        headers={"Authorization": f"Bearer {registered_user}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "美团"
