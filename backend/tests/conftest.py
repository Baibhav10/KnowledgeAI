"""
Test configuration using a real PostgreSQL test database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# Separate test database — never touches your dev data
TEST_DATABASE_URL = "postgresql://localhost/knowledge_base_ai_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    response = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123",
        "organization_name": "Test Org",
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(test_user):
    return {"Authorization": f"Bearer {test_user['access_token']}"}