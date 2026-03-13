from sqlmodel import Session, select
from app.models.db import ApiEndpoint, DbTable, AuditFinding, AuditRun
from app.audit.rules.api import missing_auth, wrong_verb, duplicate_endpoint
from app.audit.rules.database import missing_index, sensitive_column
from app.audit.rules.security import sensitive_response, exposed_token
from app.audit.rules.performance import missing_pagination, large_table_no_index

def run_audit(project_id: str, session: Session, connection_ids: list[str] | None = None) -> list[AuditFinding]:
    # Snapshot ignored findings before clearing (so we can restore them)
    old_findings = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()
    ignored_titles = {f.title for f in old_findings if f.status == "ignored"}

    for f in old_findings:
        session.delete(f)
    session.commit()

    ep_query = select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)
    tbl_query = select(DbTable).where(DbTable.project_id == project_id)
    if connection_ids:
        ep_query = ep_query.where(ApiEndpoint.connection_id.in_(connection_ids))
        tbl_query = tbl_query.where(DbTable.connection_id.in_(connection_ids))

    endpoints = session.exec(ep_query).all()
    tables = session.exec(tbl_query).all()

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
    all_findings += exposed_token.check(list(endpoints), project_id)

    # Performance rules
    all_findings += missing_pagination.check(list(endpoints), project_id)
    all_findings += large_table_no_index.check(list(tables), project_id)

    # Custom rules
    try:
        from app.models.db import CustomRule
        from app.audit.custom_rule_engine import evaluate_rule
        custom_rules = session.exec(
            select(CustomRule).where(CustomRule.project_id == project_id, CustomRule.is_active == True)
        ).all()
        for rule in custom_rules:
            if rule.rule_json:
                all_findings += evaluate_rule(rule.rule_json, list(endpoints), list(tables), project_id)
    except Exception as e:
        from sqlmodel import select as _select
        import logging
        logging.getLogger(__name__).warning(f"Custom rules evaluation failed: {e}")

    # Restore "ignored" status for matching findings
    for finding in all_findings:
        if finding.title in ignored_titles:
            finding.status = "ignored"

    for finding in all_findings:
        session.add(finding)
    session.commit()

    return all_findings
