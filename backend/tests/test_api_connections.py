"""Integration tests for /api/v1/connections endpoints."""
from unittest.mock import patch
import pytest


def _make_project(client, auth_headers, name="Conn Project"):
    return client.post("/api/v1/projects", json={"name": name}, headers=auth_headers).json()


class TestCreateConnection:
    def test_requires_auth(self, client):
        resp = client.post("/api/v1/connections", json={
            "project_id": "x", "type": "openapi", "config": {}
        })
        assert resp.status_code == 401

    def test_create_openapi_connection(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        with patch("app.api.v1.connections.ingest_connection_sync"):
            resp = client.post("/api/v1/connections", json={
                "project_id": project["id"],
                "type": "openapi",
                "config": {"url": "http://example.com/openapi.json"},
            }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "openapi"
        assert data["project_id"] == project["id"]
        assert "id" in data

    def test_create_database_connection(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        with patch("app.api.v1.connections.ingest_connection_sync"):
            resp = client.post("/api/v1/connections", json={
                "project_id": project["id"],
                "type": "database",
                "config": {"url": "postgresql://user:pass@localhost/db"},
            }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["type"] == "database"

    def test_nonexistent_project_returns_404(self, client, auth_headers):
        with patch("app.api.v1.connections.ingest_connection_sync"):
            resp = client.post("/api/v1/connections", json={
                "project_id": "ghost-id",
                "type": "openapi",
                "config": {},
            }, headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_create_connection_on_other_users_project(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        reg = client.post("/api/v1/auth/register", json={"email": "other@x.com", "password": "pass"})
        other_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        with patch("app.api.v1.connections.ingest_connection_sync"):
            resp = client.post("/api/v1/connections", json={
                "project_id": project["id"],
                "type": "openapi",
                "config": {},
            }, headers=other_headers)
        assert resp.status_code == 404


class TestListConnections:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/connections/project/some-id")
        assert resp.status_code == 401

    def test_empty_list_for_new_project(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        resp = client.get(f"/api/v1/connections/project/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_lists_created_connections(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        with patch("app.api.v1.connections.ingest_connection_sync"):
            client.post("/api/v1/connections", json={
                "project_id": project["id"], "type": "openapi", "config": {}
            }, headers=auth_headers)
            client.post("/api/v1/connections", json={
                "project_id": project["id"], "type": "database", "config": {}
            }, headers=auth_headers)

        resp = client.get(f"/api/v1/connections/project/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        conns = resp.json()
        assert len(conns) == 2
        types = {c["type"] for c in conns}
        assert types == {"openapi", "database"}

    def test_nonexistent_project_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/connections/project/ghost-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_list_other_users_connections(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        reg = client.post("/api/v1/auth/register", json={"email": "spy@x.com", "password": "pass"})
        spy_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        resp = client.get(f"/api/v1/connections/project/{project['id']}", headers=spy_headers)
        assert resp.status_code == 404
