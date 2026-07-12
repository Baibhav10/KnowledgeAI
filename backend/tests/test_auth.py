"""
Tests for authentication endpoints.
"""


def test_signup_success(client):
    response = client.post("/api/v1/auth/signup", json={
        "email": "new@example.com",
        "password": "password123",
        "organization_name": "New Org",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_signup_duplicate_email(client, test_user):
    response = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "password": "password123",
        "organization_name": "Another Org",
    })
    assert response.status_code == 409


def test_login_success(client, test_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client, test_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert response.status_code == 401


def test_get_me_authenticated(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer garbage.token.here"}
    )
    assert response.status_code == 401