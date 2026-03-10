from app.models.db import DbTable, AuditFinding

SENSITIVE_NAMES = {
    "password", "password_hash", "passwd", "secret", "token", "api_key",
    "credit_card", "card_number", "ssn", "social_security", "cvv", "pin",
    "private_key", "encryption_key",
}

def check(tables: list[DbTable], project_id: str) -> list[AuditFinding]:
    findings = []
    for table in tables:
        for col in (table.columns or []):
            col_name = col.get("name", "").lower()
            col_type = col.get("type", "").lower()
            if col_name in SENSITIVE_NAMES and ("text" in col_type or "varchar" in col_type or "char" in col_type):
                findings.append(AuditFinding(
                    project_id=project_id,
                    severity="high",
                    category="security",
                    title=f"Potentially plain-text sensitive data: {table.table_name}.{col_name}",
                    description=f"Column {col_name} in table {table.table_name} appears to store sensitive data as plain text.",
                    recommendation="Ensure sensitive data is properly hashed (passwords) or encrypted (tokens, keys). Never store passwords in plain text.",
                    resource_type="table",
                    resource_id=table.id,
                ))
    return findings
