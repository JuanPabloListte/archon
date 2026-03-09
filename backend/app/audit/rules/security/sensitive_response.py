from app.models.db import ApiEndpoint, AuditFinding

SENSITIVE_FIELD_NAMES = {"password", "secret", "token", "api_key", "private_key", "credit_card", "ssn"}

def check(endpoints: list[ApiEndpoint], project_id: str) -> list[AuditFinding]:
    findings = []
    for ep in endpoints:
        responses = ep.responses or {}
        for status_code, response in responses.items():
            if not str(status_code).startswith("2"):
                continue
            content = response.get("content", {})
            for media_type, media_schema in content.items():
                schema = media_schema.get("schema", {})
                props = schema.get("properties", {})
                for prop_name in props:
                    if prop_name.lower() in SENSITIVE_FIELD_NAMES:
                        findings.append(AuditFinding(
                            project_id=project_id,
                            severity="critical",
                            category="security",
                            title=f"Sensitive field in response: {ep.method} {ep.path} returns '{prop_name}'",
                            description=f"Endpoint {ep.method} {ep.path} exposes '{prop_name}' in its response schema.",
                            recommendation=f"Remove '{prop_name}' from the response schema. Never return sensitive data in API responses.",
                            resource_type="endpoint",
                            resource_id=ep.id,
                        ))
    return findings
