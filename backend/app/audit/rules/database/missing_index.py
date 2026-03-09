from app.models.db import DbTable, AuditFinding

LARGE_TABLE_THRESHOLD = 10_000

def check(tables: list[DbTable], project_id: str) -> list[AuditFinding]:
    findings = []
    for table in tables:
        indexes = table.indexes or []
        index_columns = set()
        for idx in indexes:
            defn = idx.get("definition", "")
            # Extract column names from index definition (simplified)
            if "(" in defn and ")" in defn:
                cols_str = defn[defn.index("(") + 1:defn.rindex(")")]
                for col in cols_str.split(","):
                    index_columns.add(col.strip().lower())

        columns = table.columns or []
        fk_columns = [fk.get("column", "").lower() for fk in (table.foreign_keys or [])]

        for fk_col in fk_columns:
            if fk_col and fk_col not in index_columns:
                findings.append(AuditFinding(
                    project_id=project_id,
                    severity="medium",
                    category="database",
                    title=f"Missing index on foreign key: {table.table_name}.{fk_col}",
                    description=f"Column {fk_col} in table {table.table_name} is a foreign key but has no index. This can cause slow JOIN queries.",
                    recommendation=f"Create an index: CREATE INDEX idx_{table.table_name}_{fk_col} ON {table.table_name}({fk_col});",
                    resource_type="table",
                    resource_id=table.id,
                ))

        if table.row_count and table.row_count > LARGE_TABLE_THRESHOLD and not indexes:
            findings.append(AuditFinding(
                project_id=project_id,
                severity="high",
                category="performance",
                title=f"Large table without indexes: {table.table_name}",
                description=f"Table {table.table_name} has {table.row_count:,} rows but no indexes. Queries will perform full table scans.",
                recommendation=f"Analyze query patterns and add appropriate indexes to {table.table_name}.",
                resource_type="table",
                resource_id=table.id,
            ))
    return findings
