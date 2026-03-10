"""Integration tests for /api/v1/projects endpoints."""
import pytest


class TestListProjects:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 401

    def test_empty_list_for_new_user(self, client, auth_headers):
        resp = client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_only_own_projects(self, client, auth_headers):
        client.post("/api/v1/projects", json={"name": "My Project"}, headers=auth_headers)

        # Register a second user and create their own project
        reg = client.post("/api/v1/auth/register", json={"email": "other@example.com", "password": "pass"})
        other_token = reg.json()["access_token"]
        client.post("/api/v1/projects", json={"name": "Other Project"},
                    headers={"Authorization": f"Bearer {other_token}"})

        resp = client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "My Project" in names
        assert "Other Project" not in names


class TestCreateProject:
    def test_requires_auth(self, client):
        resp = client.post("/api/v1/projects", json={"name": "Test"})
        assert resp.status_code == 401

    def test_create_minimal(self, client, auth_headers):
        resp = client.post("/api/v1/projects", json={"name": "API Monitor"}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "API Monitor"
        assert data["description"] is None
        assert "id" in data

    def test_create_with_description(self, client, auth_headers):
        resp = client.post("/api/v1/projects", json={
            "name": "Full Project",
            "description": "Monitors the payment API",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["description"] == "Monitors the payment API"

    def test_created_project_appears_in_list(self, client, auth_headers):
        client.post("/api/v1/projects", json={"name": "Visible"}, headers=auth_headers)
        projects = client.get("/api/v1/projects", headers=auth_headers).json()
        assert any(p["name"] == "Visible" for p in projects)


class TestGetProject:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/projects/some-id")
        assert resp.status_code == 401

    def test_get_existing_project(self, client, auth_headers):
        created = client.post("/api/v1/projects", json={"name": "Detail Test"}, headers=auth_headers).json()
        resp = client.get(f"/api/v1/projects/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Detail Test"

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/projects/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_access_other_users_project(self, client, auth_headers):
        created = client.post("/api/v1/projects", json={"name": "Private"}, headers=auth_headers).json()

        reg = client.post("/api/v1/auth/register", json={"email": "attacker@example.com", "password": "pass"})
        attacker_token = reg.json()["access_token"]

        resp = client.get(f"/api/v1/projects/{created['id']}",
                          headers={"Authorization": f"Bearer {attacker_token}"})
        assert resp.status_code == 404


class TestDeleteProject:
    def test_requires_auth(self, client):
        resp = client.delete("/api/v1/projects/some-id")
        assert resp.status_code == 401

    def test_delete_existing_project(self, client, auth_headers):
        created = client.post("/api/v1/projects", json={"name": "To Delete"}, headers=auth_headers).json()
        resp = client.delete(f"/api/v1/projects/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_deleted_project_not_in_list(self, client, auth_headers):
        created = client.post("/api/v1/projects", json={"name": "Gone"}, headers=auth_headers).json()
        client.delete(f"/api/v1/projects/{created['id']}", headers=auth_headers)
        projects = client.get("/api/v1/projects", headers=auth_headers).json()
        assert not any(p["id"] == created["id"] for p in projects)

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        resp = client.delete("/api/v1/projects/ghost-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_delete_other_users_project(self, client, auth_headers):
        created = client.post("/api/v1/projects", json={"name": "Protected"}, headers=auth_headers).json()

        reg = client.post("/api/v1/auth/register", json={"email": "bad@example.com", "password": "pass"})
        bad_token = reg.json()["access_token"]

        resp = client.delete(f"/api/v1/projects/{created['id']}",
                             headers={"Authorization": f"Bearer {bad_token}"})
        assert resp.status_code == 404
