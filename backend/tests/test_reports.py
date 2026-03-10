"""Unit tests for report generator (health score + summary)."""
import pytest
from app.models.db import AuditFinding
from app.reports.generator import calculate_health_score, _build_summary

PROJECT_ID = "proj-test-001"


def make_finding(severity: str) -> AuditFinding:
    return AuditFinding(
        project_id=PROJECT_ID,
        severity=severity,
        category="security",
        title="Test finding",
        description="desc",
        recommendation="fix it",
    )


class TestHealthScore:
    def test_no_findings_returns_100(self):
        assert calculate_health_score([]) == 100.0

    def test_single_critical(self):
        assert calculate_health_score([make_finding("critical")]) == 75.0

    def test_single_high(self):
        assert calculate_health_score([make_finding("high")]) == 85.0

    def test_single_medium(self):
        assert calculate_health_score([make_finding("medium")]) == 92.0

    def test_single_low(self):
        assert calculate_health_score([make_finding("low")]) == 97.0

    def test_single_info(self):
        assert calculate_health_score([make_finding("info")]) == 99.0

    def test_score_does_not_go_below_zero(self):
        findings = [make_finding("critical")] * 10  # 250 penalty
        assert calculate_health_score(findings) == 0.0

    def test_mixed_severities(self):
        findings = [
            make_finding("critical"),  # -25
            make_finding("high"),      # -15
            make_finding("medium"),    # -8
        ]
        assert calculate_health_score(findings) == 52.0

    def test_unknown_severity_adds_no_penalty(self):
        finding = make_finding("unknown")
        assert calculate_health_score([finding]) == 100.0


class TestBuildSummary:
    def test_low_risk_label(self):
        summary = _build_summary(85.0, {}, 10, 5)
        assert "LOW" in summary

    def test_medium_risk_label(self):
        summary = _build_summary(70.0, {}, 10, 5)
        assert "MEDIUM" in summary

    def test_high_risk_label(self):
        summary = _build_summary(50.0, {}, 10, 5)
        assert "HIGH" in summary

    def test_critical_risk_label(self):
        summary = _build_summary(30.0, {}, 10, 5)
        assert "CRITICAL" in summary

    def test_summary_includes_score(self):
        summary = _build_summary(75.0, {}, 3, 2)
        assert "75.0" in summary

    def test_summary_mentions_endpoint_and_table_counts(self):
        summary = _build_summary(90.0, {}, 12, 7)
        assert "12" in summary
        assert "7" in summary

    def test_immediate_action_when_critical_findings(self):
        summary = _build_summary(60.0, {"critical": 2, "high": 1}, 5, 3)
        assert "Immediate action" in summary

    def test_no_immediate_action_without_critical(self):
        summary = _build_summary(80.0, {"high": 1}, 5, 3)
        assert "Immediate action" not in summary
