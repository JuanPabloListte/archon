"""Integration tests for /api/v1/dashboard endpoints."""
import pytest
from app.models.db import AuditFinding, Report


def _make_project(client, auth_headers, name="Stats Project"):
    return client.post("/api/v1/projects", json={"name": name}, headers=auth_headers).json()


def _seed_report(session, project_id, health_score=80.0):
    r = Report(project_id=project_id, health_score=health_score, summary="ok", report_json={})
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


def _seed_finding(session, project_id):
    f = AuditFinding(
        project_id=project_id, severity="high", category="security",
        title="T", description="D", recommendation="R",
    )
    session.add(f)
    session.commit()


class TestDashboardStats:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 401

    def test_empty_stats_for_new_user(self, client, auth_headers):
        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] == 0
        assert data["total_findings"] == 0
        assert data["avg_health_score"] is None
        assert data["projects_audited"] == 0

    def test_counts_projects(self, client, auth_headers):
        _make_project(client, auth_headers, "P1")
        _make_project(client, auth_headers, "P2")
        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.json()["total_projects"] == 2

    def test_counts_findings(self, client, session, auth_headers):
        p = _make_project(client, auth_headers)
        _seed_finding(session, p["id"])
        _seed_finding(session, p["id"])
        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.json()["total_findings"] == 2

    def test_avg_health_score_from_reports(self, client, session, auth_headers):
        p1 = _make_project(client, auth_headers, "P1")
        p2 = _make_project(client, auth_headers, "P2")
        _seed_report(session, p1["id"], health_score=80.0)
        _seed_report(session, p2["id"], health_score=60.0)
        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        data = resp.json()
        assert data["projects_audited"] == 2
        assert data["avg_health_score"] == 70.0

    def test_only_counts_own_data(self, client, session, auth_headers):
        p = _make_project(client, auth_headers)
        _seed_finding(session, p["id"])

        reg = client.post("/api/v1/auth/register", json={"email": "other@x.com", "password": "pass"})
        other_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        resp = client.get("/api/v1/dashboard/stats", headers=other_headers)
        data = resp.json()
        assert data["total_projects"] == 0
        assert data["total_findings"] == 0
