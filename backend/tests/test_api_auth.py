"""Integration tests for /api/v1/auth endpoints."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "pass123"}
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_returns_usable_token(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "tokentest@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        projects_resp = client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert projects_resp.status_code == 200


class TestLogin:
    def test_login_success(self, client, user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com",
            "password": "pass123",
        })
        assert resp.status_code == 401

    def test_login_returns_usable_token(self, client, user):
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        token = login_resp.json()["access_token"]
        projects_resp = client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert projects_resp.status_code == 200
