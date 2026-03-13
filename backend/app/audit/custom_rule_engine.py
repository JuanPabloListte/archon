"""Evaluates declarative custom rules (YAML/JSON) against project data."""
import re
import logging
from typing import Any
from app.models.db import AuditFinding, ApiEndpoint, DbTable

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"api", "database", "security", "performance"}
VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
VALID_TARGETS = {"endpoints", "tables"}
VALID_OPERATORS = {"eq", "neq", "contains", "not_contains", "starts_with", "ends_with", "gt", "lt", "gte", "lte", "is_empty", "is_not_empty", "matches_regex"}


def validate_rule_schema(rule: dict) -> list[str]:
    errors = []
    if not rule.get("name"):
        errors.append("'name' is required")
    if rule.get("category", "security") not in VALID_CATEGORIES:
        errors.append(f"'category' must be one of: {', '.join(VALID_CATEGORIES)}")
    if rule.get("severity", "medium") not in VALID_SEVERITIES:
        errors.append(f"'severity' must be one of: {', '.join(VALID_SEVERITIES)}")
    if rule.get("target", "endpoints") not in VALID_TARGETS:
        errors.append(f"'target' must be one of: {', '.join(VALID_TARGETS)}")
    if rule.get("match", "all") not in ("all", "any"):
        errors.append("'match' must be 'all' or 'any'")
    conditions = rule.get("conditions", [])
    if not conditions:
        errors.append("at least one condition is required")
    for i, cond in enumerate(conditions):
        if not cond.get("field"):
            errors.append(f"condition[{i}]: 'field' is required")
        op = cond.get("operator")
        if op not in VALID_OPERATORS:
            errors.append(f"condition[{i}]: 'operator' must be one of: {', '.join(VALID_OPERATORS)}")
        if op == "matches_regex":
            try:
                re.compile(str(cond.get("value", "")))
            except re.error as e:
                errors.append(f"condition[{i}]: invalid regex — {e}")
    if not rule.get("finding_title"):
        errors.append("'finding_title' is required")
    return errors


def _get_field(item: Any, field: str) -> Any:
    """Extract a field from an endpoint or table object."""
    return getattr(item, field, None)


def _apply_operator(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "is_empty":
        return actual is None or actual == "" or actual == [] or actual == {}
    if operator == "is_not_empty":
        return actual is not None and actual != "" and actual != [] and actual != {}
    if actual is None:
        return False
    s = str(actual).lower()
    e = str(expected).lower() if expected is not None else ""
    if operator == "eq":       return s == e
    if operator == "neq":      return s != e
    if operator == "contains": return e in s
    if operator == "not_contains": return e not in s
    if operator == "starts_with":  return s.startswith(e)
    if operator == "ends_with":    return s.endswith(e)
    if operator == "matches_regex":
        try:
            return bool(re.search(e, s, re.IGNORECASE))
        except re.error:
            return False
    try:
        a_num, e_num = float(actual), float(expected)
        if operator == "gt":  return a_num > e_num
        if operator == "lt":  return a_num < e_num
        if operator == "gte": return a_num >= e_num
        if operator == "lte": return a_num <= e_num
    except (ValueError, TypeError):
        pass
    return False


def _item_matches(item: Any, conditions: list[dict], match: str) -> bool:
    results = [
        _apply_operator(_get_field(item, c["field"]), c["operator"], c.get("value"))
        for c in conditions
    ]
    return all(results) if match == "all" else any(results)


def _interpolate(template: str, item: Any) -> str:
    try:
        attrs = {k: getattr(item, k, "") for k in vars(item.__class__) if not k.startswith("_")}
        # Also add instance attributes
        if hasattr(item, "__dict__"):
            attrs.update({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
        return template.format_map({k: (v or "") for k, v in attrs.items()})
    except Exception:
        return template


def evaluate_rule(
    rule: dict,
    endpoints: list[ApiEndpoint],
    tables: list[DbTable],
    project_id: str,
) -> list[AuditFinding]:
    findings = []
    target = rule.get("target", "endpoints")
    conditions = rule.get("conditions", [])
    match = rule.get("match", "all")
    severity = rule.get("severity", "medium")
    category = rule.get("category", "security")

    items = endpoints if target == "endpoints" else tables

    for item in items:
        try:
            if _item_matches(item, conditions, match):
                title = _interpolate(rule.get("finding_title", rule["name"]), item)
                description = _interpolate(rule.get("finding_description", ""), item)
                recommendation = _interpolate(rule.get("finding_recommendation", ""), item)
                findings.append(AuditFinding(
                    project_id=project_id,
                    severity=severity,
                    category=category,
                    title=title,
                    description=description or title,
                    recommendation=recommendation or "Review and fix this issue.",
                    source="rule",
                ))
        except Exception as e:
            logger.warning(f"Custom rule '{rule.get('name')}' error on item: {e}")

    return findings
