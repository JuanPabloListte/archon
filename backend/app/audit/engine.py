from sqlmodel import Session, select
from app.models.db import ApiEndpoint, DbTable, AuditFinding
from app.audit.rules.api import missing_auth, wrong_verb, duplicate_endpoint
from app.audit.rules.database import missing_index, sensitive_column
from app.audit.rules.security import sensitive_response

def run_audit(project_id: str, session: Session) -> list[AuditFinding]:
    # Clear previous findings
    old_findings = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()
    for f in old_findings:
        session.delete(f)
    session.commit()

    endpoints = session.exec(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)).all()
    tables = session.exec(select(DbTable).where(DbTable.project_id == project_id)).all()

    all_findings: list[AuditFinding] = []

    # API rules
    all_findings += missing_auth.check(list(endpoints), project_id)
    all_findings += wrong_verb.check(list(endpoints), project_id)
    all_findings += duplicate_endpoint.check(list(endpoints), project_id)

    # Database rules
    all_findings += missing_index.check(list(tables), project_id)
    all_findings += sensitive_column.check(list(tables), project_id)

    # Security rules
    all_findings += sensitive_response.check(list(endpoints), project_id)

    for finding in all_findings:
        session.add(finding)
    session.commit()

    return all_findings
