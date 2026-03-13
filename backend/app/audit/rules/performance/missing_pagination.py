from app.models.db import ApiEndpoint, AuditFinding

PAGINATION_PARAMS = {"page", "limit", "offset", "per_page", "cursor", "size", "skip", "take"}

def _looks_like_list_endpoint(ep: ApiEndpoint) -> bool:
    """Heuristic: GET endpoint whose path segment ends in a plural noun or contains /list /all /search."""
    if ep.method.upper() != "GET":
        return False
    path_lower = ep.path.lower().rstrip("/")
    last_segment = path_lower.split("/")[-1]
    # Skip if it has a path parameter (single-resource endpoint)
    if "{" in last_segment:
        return False
    # Check list-like keywords or plural ending
    if any(kw in path_lower for kw in ["/list", "/all", "/search", "/feed", "/items"]):
        return True
    if last_segment.endswith("s") and len(last_segment) > 2:
        return True
    return False

def _has_pagination(ep: ApiEndpoint) -> bool:
    params = ep.parameters or []
    param_names = {p.get("name", "").lower() for p in params if isinstance(p, dict)}
    return bool(param_names & PAGINATION_PARAMS)

def check(endpoints: list[ApiEndpoint], project_id: str) -> list[AuditFinding]:
    findings = []
    for ep in endpoints:
        if _looks_like_list_endpoint(ep) and not _has_pagination(ep):
            findings.append(AuditFinding(
                project_id=project_id,
                severity="medium",
                category="performance",
                title=f"Missing pagination on {ep.method} {ep.path}",
                description=(
                    f"The endpoint {ep.method} {ep.path} appears to return a collection "
                    "but has no pagination parameters (page, limit, offset, cursor, etc.). "
                    "This can cause slow responses and excessive memory usage as data grows."
                ),
                recommendation=(
                    "Add pagination parameters such as `page` + `limit` or a `cursor`. "
                    "Return paginated results with total count metadata. "
                    "Consider defaulting `limit` to 50 and enforcing a maximum of 500."
                ),
                resource_type="endpoint",
                resource_id=ep.id,
            ))
    return findings
