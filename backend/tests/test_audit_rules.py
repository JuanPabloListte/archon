"""Unit tests for all audit rules.

Rules are pure functions that receive lists of model instances and return
AuditFinding objects — no database required.
"""
import pytest
from app.models.db import ApiEndpoint, DbTable, AuditFinding
from app.audit.rules.api import missing_auth, wrong_verb, duplicate_endpoint
from app.audit.rules.database import missing_index, sensitive_column
from app.audit.rules.security import sensitive_response

PROJECT_ID = "proj-test-001"


def make_endpoint(**kwargs) -> ApiEndpoint:
    defaults = dict(
        id="ep-1",
        project_id=PROJECT_ID,
        path="/items",
        method="GET",
        auth_required=False,
        responses={},
        parameters={},
        tags=[],
    )
    defaults.update(kwargs)
    return ApiEndpoint(**defaults)


def make_table(**kwargs) -> DbTable:
    defaults = dict(
        id="tbl-1",
        project_id=PROJECT_ID,
        table_name="items",
        row_count=0,
        columns=[],
        indexes=[],
        foreign_keys=[],
    )
    defaults.update(kwargs)
    return DbTable(**defaults)


# ── missing_auth ─────────────────────────────────────────────────────────────

class TestMissingAuth:
    def test_post_without_auth_raises_finding(self):
        ep = make_endpoint(method="POST", path="/items", auth_required=False)
        findings = missing_auth.check([ep], PROJECT_ID)
        assert len(findings) == 1
        assert findings[0].severity == "high"
        assert "POST" in findings[0].title

    def test_put_without_auth_raises_finding(self):
        ep = make_endpoint(method="PUT", path="/items/1", auth_required=False)
        findings = missing_auth.check([ep], PROJECT_ID)
        assert len(findings) == 1

    def test_delete_without_auth_raises_finding(self):
        ep = make_endpoint(method="DELETE", path="/items/1", auth_required=False)
        findings = missing_auth.check([ep], PROJECT_ID)
        assert len(findings) == 1

    def test_post_with_auth_is_clean(self):
        ep = make_endpoint(method="POST", path="/items", auth_required=True)
        findings = missing_auth.check([ep], PROJECT_ID)
        assert findings == []

    def test_get_without_auth_is_clean(self):
        ep = make_endpoint(method="GET", path="/items", auth_required=False)
        findings = missing_auth.check([ep], PROJECT_ID)
        assert findings == []

    def test_multiple_endpoints_mixed(self):
        endpoints = [
            make_endpoint(id="e1", method="POST", path="/a", auth_required=False),
            make_endpoint(id="e2", method="POST", path="/b", auth_required=True),
            make_endpoint(id="e3", method="GET",  path="/c", auth_required=False),
            make_endpoint(id="e4", method="DELETE", path="/d", auth_required=False),
        ]
        findings = missing_auth.check(endpoints, PROJECT_ID)
        assert len(findings) == 2  # /a and /d


# ── wrong_verb ───────────────────────────────────────────────────────────────

class TestWrongVerb:
    def test_get_on_create_path(self):
        ep = make_endpoint(method="GET", path="/users/create")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert len(findings) == 1
        assert findings[0].severity == "medium"

    def test_get_on_add_path(self):
        ep = make_endpoint(method="GET", path="/items/add")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert len(findings) == 1

    def test_get_on_delete_path(self):
        ep = make_endpoint(method="GET", path="/items/delete")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_get_on_remove_path(self):
        ep = make_endpoint(method="GET", path="/orders/remove")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert len(findings) == 1

    def test_post_on_create_path_is_clean(self):
        ep = make_endpoint(method="POST", path="/users/create")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert findings == []

    def test_get_on_normal_path_is_clean(self):
        ep = make_endpoint(method="GET", path="/users/1")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert findings == []

    def test_delete_on_delete_path_is_clean(self):
        ep = make_endpoint(method="DELETE", path="/items/delete/1")
        findings = wrong_verb.check([ep], PROJECT_ID)
        assert findings == []


# ── duplicate_endpoint ───────────────────────────────────────────────────────

class TestDuplicateEndpoint:
    def test_detects_exact_duplicate(self):
        endpoints = [
            make_endpoint(id="e1", method="GET", path="/items"),
            make_endpoint(id="e2", method="GET", path="/items"),
        ]
        findings = duplicate_endpoint.check(endpoints, PROJECT_ID)
        assert len(findings) == 1
        assert "GET" in findings[0].title
        assert "/items" in findings[0].title

    def test_same_path_different_method_is_clean(self):
        endpoints = [
            make_endpoint(id="e1", method="GET", path="/items"),
            make_endpoint(id="e2", method="POST", path="/items"),
        ]
        findings = duplicate_endpoint.check(endpoints, PROJECT_ID)
        assert findings == []

    def test_no_duplicates_is_clean(self):
        endpoints = [
            make_endpoint(id="e1", method="GET",  path="/a"),
            make_endpoint(id="e2", method="POST", path="/b"),
            make_endpoint(id="e3", method="PUT",  path="/c"),
        ]
        findings = duplicate_endpoint.check(endpoints, PROJECT_ID)
        assert findings == []

    def test_triple_duplicate(self):
        endpoints = [make_endpoint(id=f"e{i}", method="POST", path="/x") for i in range(3)]
        findings = duplicate_endpoint.check(endpoints, PROJECT_ID)
        assert len(findings) == 1
        assert "3" in findings[0].description


# ── missing_index ─────────────────────────────────────────────────────────────

class TestMissingIndex:
    def test_fk_column_without_index(self):
        table = make_table(
            table_name="orders",
            foreign_keys=[{"column": "user_id"}],
            indexes=[],
        )
        findings = missing_index.check([table], PROJECT_ID)
        assert len(findings) == 1
        assert "user_id" in findings[0].title
        assert findings[0].severity == "medium"

    def test_fk_column_with_index_is_clean(self):
        table = make_table(
            table_name="orders",
            foreign_keys=[{"column": "user_id"}],
            indexes=[{"definition": "CREATE INDEX idx ON orders(user_id)"}],
        )
        findings = missing_index.check([table], PROJECT_ID)
        assert findings == []

    def test_large_table_without_indexes(self):
        table = make_table(
            table_name="events",
            row_count=50_000,
            indexes=[],
            foreign_keys=[],
        )
        findings = missing_index.check([table], PROJECT_ID)
        assert len(findings) == 1
        assert findings[0].severity == "high"
        assert "events" in findings[0].title

    def test_large_table_with_indexes_is_clean(self):
        table = make_table(
            table_name="events",
            row_count=50_000,
            indexes=[{"definition": "CREATE INDEX idx ON events(created_at)"}],
            foreign_keys=[],
        )
        findings = missing_index.check([table], PROJECT_ID)
        assert findings == []

    def test_small_table_without_indexes_is_clean(self):
        table = make_table(row_count=100, indexes=[], foreign_keys=[])
        findings = missing_index.check([table], PROJECT_ID)
        assert findings == []


# ── sensitive_column ──────────────────────────────────────────────────────────

class TestSensitiveColumn:
    def test_plain_password_column(self):
        table = make_table(
            table_name="users",
            columns=[{"name": "password", "type": "varchar(255)"}],
        )
        findings = sensitive_column.check([table], PROJECT_ID)
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_token_column(self):
        table = make_table(
            table_name="sessions",
            columns=[{"name": "token", "type": "text"}],
        )
        findings = sensitive_column.check([table], PROJECT_ID)
        assert len(findings) == 1

    def test_safe_column_is_clean(self):
        table = make_table(
            table_name="users",
            columns=[
                {"name": "email", "type": "varchar(255)"},
                {"name": "created_at", "type": "timestamp"},
            ],
        )
        findings = sensitive_column.check([table], PROJECT_ID)
        assert findings == []

    def test_api_key_column(self):
        table = make_table(
            table_name="integrations",
            columns=[{"name": "api_key", "type": "varchar(100)"}],
        )
        findings = sensitive_column.check([table], PROJECT_ID)
        assert len(findings) == 1


# ── sensitive_response ────────────────────────────────────────────────────────

class TestSensitiveResponse:
    def _make_response_endpoint(self, prop_name: str, status="200") -> ApiEndpoint:
        return make_endpoint(
            method="GET",
            path="/me",
            responses={
                status: {
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {prop_name: {"type": "string"}}
                            }
                        }
                    }
                }
            },
        )

    def test_password_in_response(self):
        ep = self._make_response_endpoint("password")
        findings = sensitive_response.check([ep], PROJECT_ID)
        assert len(findings) == 1
        assert findings[0].severity == "critical"

    def test_token_in_response(self):
        ep = self._make_response_endpoint("token")
        findings = sensitive_response.check([ep], PROJECT_ID)
        assert len(findings) == 1

    def test_safe_field_is_clean(self):
        ep = self._make_response_endpoint("email")
        findings = sensitive_response.check([ep], PROJECT_ID)
        assert findings == []

    def test_sensitive_field_in_4xx_is_clean(self):
        """Error responses exposing sensitive fields should NOT be flagged."""
        ep = self._make_response_endpoint("secret", status="400")
        findings = sensitive_response.check([ep], PROJECT_ID)
        assert findings == []

    def test_no_responses_is_clean(self):
        ep = make_endpoint(responses={})
        findings = sensitive_response.check([ep], PROJECT_ID)
        assert findings == []
