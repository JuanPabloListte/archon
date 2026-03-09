from app.models.db import ApiEndpoint, AuditFinding

def check(endpoints: list[ApiEndpoint], project_id: str) -> list[AuditFinding]:
    findings = []
    for ep in endpoints:
        path_lower = ep.path.lower()
        if ep.method == "GET" and any(kw in path_lower for kw in ["/create", "/add", "/new", "/insert"]):
            findings.append(AuditFinding(
                project_id=project_id,
                severity="medium",
                category="api",
                title=f"Wrong HTTP verb on {ep.path}",
                description=f"Endpoint {ep.path} uses GET but path suggests a creation operation. GET should be idempotent and not cause side effects.",
                recommendation="Use POST for resource creation operations.",
                resource_type="endpoint",
                resource_id=ep.id,
            ))
        if ep.method == "GET" and any(kw in path_lower for kw in ["/delete", "/remove", "/destroy"]):
            findings.append(AuditFinding(
                project_id=project_id,
                severity="high",
                category="api",
                title=f"Destructive operation via GET on {ep.path}",
                description=f"Endpoint {ep.path} uses GET but path suggests a destructive operation.",
                recommendation="Use DELETE for resource deletion operations.",
                resource_type="endpoint",
                resource_id=ep.id,
            ))
    return findings
