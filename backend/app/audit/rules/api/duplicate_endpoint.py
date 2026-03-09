from app.models.db import ApiEndpoint, AuditFinding
from collections import Counter

def check(endpoints: list[ApiEndpoint], project_id: str) -> list[AuditFinding]:
    findings = []
    seen = Counter()
    for ep in endpoints:
        key = (ep.method, ep.path)
        seen[key] += 1
    for (method, path), count in seen.items():
        if count > 1:
            findings.append(AuditFinding(
                project_id=project_id,
                severity="medium",
                category="api",
                title=f"Duplicate endpoint: {method} {path}",
                description=f"Endpoint {method} {path} is defined {count} times in the API spec.",
                recommendation="Remove duplicate endpoint definitions. Keep only one definition per endpoint.",
                resource_type="endpoint",
                resource_id=None,
            ))
    return findings
