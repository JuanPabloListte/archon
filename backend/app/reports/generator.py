from sqlmodel import Session, select
from app.models.db import Project, ApiEndpoint, DbTable, AuditFinding, Report
from datetime import datetime

SEVERITY_WEIGHTS = {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 1}

def calculate_health_score(findings: list[AuditFinding]) -> float:
    if not findings:
        return 100.0
    total_penalty = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in findings)
    score = max(0.0, 100.0 - total_penalty)
    return round(score, 1)

def generate_report(project_id: str, session: Session) -> Report:
    project = session.exec(select(Project).where(Project.id == project_id)).first()
    endpoints = session.exec(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)).all()
    tables = session.exec(select(DbTable).where(DbTable.project_id == project_id)).all()
    findings = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()

    findings_list = list(findings)
    health_score = calculate_health_score(findings_list)

    severity_counts = {}
    for f in findings_list:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    category_counts = {}
    for f in findings_list:
        category_counts[f.category] = category_counts.get(f.category, 0) + 1

    report_json = {
        "generated_at": datetime.utcnow().isoformat(),
        "project": {"id": project.id, "name": project.name},
        "overview": {
            "total_endpoints": len(list(endpoints)),
            "total_tables": len(list(tables)),
            "total_findings": len(findings_list),
            "health_score": health_score,
        },
        "findings_by_severity": severity_counts,
        "findings_by_category": category_counts,
        "findings": [
            {
                "id": f.id,
                "severity": f.severity,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "recommendation": f.recommendation,
            }
            for f in sorted(findings_list, key=lambda x: list(SEVERITY_WEIGHTS.keys()).index(x.severity) if x.severity in SEVERITY_WEIGHTS else 99)
        ],
    }

    summary = _build_summary(health_score, severity_counts, len(list(endpoints)), len(list(tables)))

    report = Report(
        project_id=project_id,
        health_score=health_score,
        summary=summary,
        report_json=report_json,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report

def _build_summary(health_score: float, severity_counts: dict, endpoint_count: int, table_count: int) -> str:
    critical = severity_counts.get("critical", 0)
    high = severity_counts.get("high", 0)
    total = sum(severity_counts.values())

    risk_level = "LOW" if health_score >= 80 else "MEDIUM" if health_score >= 60 else "HIGH" if health_score >= 40 else "CRITICAL"

    return (
        f"System health score: {health_score}/100 ({risk_level} risk). "
        f"Analyzed {endpoint_count} API endpoints and {table_count} database tables. "
        f"Found {total} issues ({critical} critical, {high} high severity). "
        f"{'Immediate action required.' if critical > 0 else 'Review and address findings by priority.'}"
    )
