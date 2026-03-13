from app.models.db import ApiEndpoint, AuditFinding

# Paths that suggest token/secret exposure via GET
SENSITIVE_PATH_KEYWORDS = {"token", "secret", "api-key", "apikey", "private-key", "credential", "auth-token"}

def check(endpoints: list[ApiEndpoint], project_id: str) -> list[AuditFinding]:
    findings = []
    for ep in endpoints:
        if ep.method.upper() != "GET":
            continue
        path_lower = ep.path.lower()
        segments = set(path_lower.strip("/").split("/"))
        matched = segments & SENSITIVE_PATH_KEYWORDS
        if matched and not ep.auth_required:
            keyword = next(iter(matched))
            findings.append(AuditFinding(
                project_id=project_id,
                severity="critical",
                category="security",
                title=f"Unauthenticated endpoint may expose secrets: GET {ep.path}",
                description=(
                    f"The endpoint GET {ep.path} contains '{keyword}' in its path and does not require "
                    "authentication. This may allow unauthenticated users to retrieve sensitive credentials or tokens."
                ),
                recommendation=(
                    "Require authentication on this endpoint. "
                    "Verify that sensitive tokens or credentials are never returned in plain text. "
                    "Consider whether this endpoint should exist at all — tokens should be issued, not retrieved."
                ),
                resource_type="endpoint",
                resource_id=ep.id,
            ))
    return findings
