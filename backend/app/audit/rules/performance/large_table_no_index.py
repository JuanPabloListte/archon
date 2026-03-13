from app.models.db import DbTable, AuditFinding

ROW_THRESHOLD = 10_000

def check(tables: list[DbTable], project_id: str) -> list[AuditFinding]:
    findings = []
    for table in tables:
        row_count = table.row_count or 0
        if row_count < ROW_THRESHOLD:
            continue
        indexes = table.indexes or []
        # Count non-primary-key indexes
        non_pk_indexes = [
            idx for idx in indexes
            if isinstance(idx, dict) and not idx.get("primary", False)
        ]
        if len(non_pk_indexes) == 0:
            findings.append(AuditFinding(
                project_id=project_id,
                severity="high",
                category="performance",
                title=f"Large table '{table.table_name}' has no indexes ({row_count:,} rows)",
                description=(
                    f"Table '{table.table_name}' has {row_count:,} rows but no secondary indexes. "
                    "Full table scans on large tables cause slow queries and degrade overall DB performance."
                ),
                recommendation=(
                    "Analyze the most common query patterns and add indexes on frequently filtered, "
                    "sorted, or joined columns. Start with foreign keys and columns used in WHERE clauses. "
                    "Use `EXPLAIN ANALYZE` to identify slow queries."
                ),
                resource_type="table",
                resource_id=table.id,
            ))
    return findings
