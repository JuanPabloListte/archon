import httpx
import yaml
import json
from typing import Optional
from sqlmodel import Session
from app.models.db import ApiEndpoint

SENSITIVE_PARAMS = {"password", "token", "secret", "api_key", "apikey", "authorization", "auth"}

def _has_security(operation: dict, global_security: list) -> bool:
    op_security = operation.get("security")
    if op_security is not None:
        return len(op_security) > 0
    return len(global_security) > 0

async def parse_openapi(url: str, project_id: str, session: Session, extra_headers: dict = None, connection_id: str = None):
    async with httpx.AsyncClient() as client:
        headers = extra_headers or {}
        resp = await client.get(url, headers=headers, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "yaml" in content_type or url.endswith((".yaml", ".yml")):
            spec = yaml.safe_load(resp.text)
        else:
            spec = resp.json()

    _process_spec(spec, project_id, session, connection_id=connection_id)

def parse_openapi_content(content: str | dict, project_id: str, session: Session, connection_id: str = None):
    if isinstance(content, str):
        try:
            spec = json.loads(content)
        except json.JSONDecodeError:
            spec = yaml.safe_load(content)
    else:
        spec = content
    _process_spec(spec, project_id, session, connection_id=connection_id)

def _process_spec(spec: dict, project_id: str, session: Session, connection_id: str = None):
    global_security = spec.get("security", [])
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            operation = path_item.get(method)
            if not operation:
                continue

            auth_required = _has_security(operation, global_security)
            description = operation.get("summary") or operation.get("description") or ""
            parameters = operation.get("parameters", [])
            responses = operation.get("responses", {})
            tags = operation.get("tags", [])

            endpoint = ApiEndpoint(
                project_id=project_id,
                connection_id=connection_id,
                path=path,
                method=method.upper(),
                auth_required=auth_required,
                description=description,
                parameters=parameters,
                responses=responses,
                tags=tags,
            )
            session.add(endpoint)

    session.commit()
