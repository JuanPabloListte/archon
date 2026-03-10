"""Integration tests for /api/v1/audits endpoints."""
from unittest.mock import AsyncMock, patch
import pytest


def _make_project(client, auth_headers, name="Audit Project"):
    return client.post("/api/v1/projects", json={"name": name}, headers=auth_headers).json()


def _seed_finding(session, project_id):
    from app.models.db import AuditFinding
    f = AuditFinding(
        project_id=project_id,
        severity="high",
        category="security",
        title="Test finding",
        description="desc",
        recommendation="fix it",
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


class TestRunAudit:
    def test_requires_auth(self, client):
        resp = client.post("/api/v1/audits/run/some-id")
        assert resp.status_code == 401

    def test_run_on_nonexistent_project_returns_404(self, client, auth_headers):
        resp = client.post("/api/v1/audits/run/ghost-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_run_audit_triggers_background_task(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        with patch("app.api.v1.audits.run_audit_sync"):
            resp = client.post(f"/api/v1/audits/run/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project["id"]
        assert "started" in data["message"].lower()

    def test_cannot_run_audit_on_other_users_project(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        reg = client.post("/api/v1/auth/register", json={"email": "other@x.com", "password": "pass"})
        other_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        resp = client.post(f"/api/v1/audits/run/{project['id']}", headers=other_headers)
        assert resp.status_code == 404


class TestGetFindings:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/audits/findings/some-id")
        assert resp.status_code == 401

    def test_empty_findings_for_new_project(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        resp = client.get(f"/api/v1/audits/findings/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_seeded_findings(self, client, session, auth_headers):
        project = _make_project(client, auth_headers)
        _seed_finding(session, project["id"])
        resp = client.get(f"/api/v1/audits/findings/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        findings = resp.json()
        assert len(findings) == 1
        assert findings[0]["severity"] == "high"
        assert findings[0]["title"] == "Test finding"

    def test_nonexistent_project_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/audits/findings/ghost-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_access_other_users_findings(self, client, session, auth_headers):
        project = _make_project(client, auth_headers)
        _seed_finding(session, project["id"])
        reg = client.post("/api/v1/auth/register", json={"email": "spy@x.com", "password": "pass"})
        spy_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        resp = client.get(f"/api/v1/audits/findings/{project['id']}", headers=spy_headers)
        assert resp.status_code == 404


class TestInsights:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/audits/insights/some-id")
        assert resp.status_code == 401

    def test_nonexistent_project_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/audits/insights/ghost-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_no_findings_returns_empty_insights(self, client, auth_headers):
        project = _make_project(client, auth_headers)
        mock_result = {"prioritized": [], "summary": "No findings to analyze."}
        with patch("app.agents.auditor_agent.AuditorAgent.prioritize_findings", new=AsyncMock(return_value=mock_result)):
            resp = client.get(f"/api/v1/audits/insights/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["prioritized"] == []

    def test_returns_prioritized_findings(self, client, session, auth_headers):
        project = _make_project(client, auth_headers)
        finding = _seed_finding(session, project["id"])
        mock_result = {
            "prioritized": [{"id": finding.id, "severity": "high", "title": "Test finding"}],
            "summary": "One high severity issue found.",
        }
        with patch("app.agents.auditor_agent.AuditorAgent.prioritize_findings", new=AsyncMock(return_value=mock_result)):
            resp = client.get(f"/api/v1/audits/insights/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["prioritized"]) == 1
        assert "high" in data["summary"] or "issue" in data["summary"]


class TestFindingAdvice:
    def test_requires_auth(self, client):
        resp = client.get("/api/v1/audits/findings/some-id/advice")
        assert resp.status_code == 401

    def test_nonexistent_finding_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/audits/findings/ghost-id/advice", headers=auth_headers)
        assert resp.status_code == 404

    def test_returns_recommendations(self, client, session, auth_headers):
        project = _make_project(client, auth_headers)
        finding = _seed_finding(session, project["id"])
        mock_result = {"finding_id": finding.id, "recommendations": "Apply authentication middleware."}
        with patch("app.agents.advisor_agent.AdvisorAgent.get_recommendations", new=AsyncMock(return_value=mock_result)):
            resp = client.get(f"/api/v1/audits/findings/{finding.id}/advice", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["finding_id"] == finding.id
        assert len(data["recommendations"]) > 0

    def test_cannot_get_advice_for_other_users_finding(self, client, session, auth_headers):
        project = _make_project(client, auth_headers)
        finding = _seed_finding(session, project["id"])
        reg = client.post("/api/v1/auth/register", json={"email": "attacker@x.com", "password": "pass"})
        attacker_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        resp = client.get(f"/api/v1/audits/findings/{finding.id}/advice", headers=attacker_headers)
        assert resp.status_code == 404
