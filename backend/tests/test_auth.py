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

def test_register_user():
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123", "nickname": "TestUser"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["nickname"] == "TestUser"
    assert "id" in data

def test_register_duplicate_email():
    client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123", "nickname": "TestUser"}
    )
    response = client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password456", "nickname": "AnotherUser"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_user():
    client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "password123", "nickname": "LoginUser"}
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password():
    client.post(
        "/api/auth/register",
        json={"email": "invalid@example.com", "password": "password123", "nickname": "InvalidUser"}
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "invalid@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
