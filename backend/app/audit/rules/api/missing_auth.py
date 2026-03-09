from app.models.db import ApiEndpoint, AuditFinding

METHODS_REQUIRING_AUTH = {"POST", "PUT", "PATCH", "DELETE"}

def check(endpoints: list[ApiEndpoint], project_id: str) -> list[AuditFinding]:
    findings = []
    for ep in endpoints:
        if ep.method in METHODS_REQUIRING_AUTH and not ep.auth_required:
            findings.append(AuditFinding(
                project_id=project_id,
                severity="high",
                category="security",
                title=f"Missing authentication on {ep.method} {ep.path}",
                description=f"The endpoint {ep.method} {ep.path} modifies data but does not require authentication.",
                recommendation="Add authentication/authorization to this endpoint using JWT, OAuth2, or API keys.",
                resource_type="endpoint",
                resource_id=ep.id,
            ))
    return findings
